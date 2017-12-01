#!/usr/bin/env python


import requests
import os
import json
import yaml

import argparse
import sys

import pprint
import time

OS_AUTH = {
    "OS_USERNAME": "",
    "OS_PASSWORD": "",
    "OS_PROJECT_NAME": "",
    "OS_PROJECT_ID": "",
    "OS_AUTH_URL": "",
    "OS_REGION_NAME": "",
    "OS_IDENTITY_API_VERSION": "",
    "OS_USER_DOMAIN_NAME": "",
    "OS_PROJECT_DOMAIN_NAME": ""
}

default_json = {
        "_meta": {
            "hostvars": {}
        },
    }


def get_regional_token():
    session = requests.Session()
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    os_user_domain = OS_AUTH['OS_USER_DOMAIN_NAME']
    os_username = OS_AUTH['OS_USERNAME']
    os_password = OS_AUTH['OS_PASSWORD']
    # In the V3 identity API a project_name is only unique within a domain 
    # so you must also provide either a project_domain_id or project_domain_name.
    os_project_id = OS_AUTH['OS_PROJECT_ID']
    os_auth_url = OS_AUTH['OS_AUTH_URL'] 
    
    if os_project_id == "":
        print "OS_PROJECT_ID must be defined"
        sys.exit(1)

    if os_auth_url == "":
        print "OS_AUTH_URL must be defined"
        sys.exit(1)

    url = os_auth_url + '/auth/tokens'
    query_json = {'auth': {
                            'identity': {
                                'methods': ['password'],
                                'password': {
                                    'user': {
                                        'domain': {
                                            'name': os_user_domain
                                        },
                                        'name': os_username,
                                        'password': os_password
                                    }
                                }
                            },
                            "scope": {
                                "project": {
                                    "id": os_project_id
                                }
                            }
                       }
                    }
    try:
        response = session.request('POST', url, headers=headers, json=query_json)
    except requests.exceptions.RequestException as e:
        print e
        sys.exit(1)

    # we failed to authenticate
    if response.status_code not in (201,):
        print "RESP: HTTP Code:" + str(response.status_code) + " " + str(response.content)
        sys.exit(1)

    # we authenticated, now check the token is present
    if 'X-Subject-Token' in response.headers.keys():
        auth_token = response.headers['X-Subject-Token']
    elif 'x-subject-token' in response.headers.keys():      # fix for issue #1
        auth_token = response.headers['x-subject-token']
    else:
        print "Token not found"
        sys.exit(1)

    endpoints = response.json()['token']['catalog']
    return auth_token, endpoints

def create_config_from_config(config_file):
    """
    This reads from the openstack.yaml produced by AWX/Ansible Tower

    cache:
      path: /tmp/awx_43_XFBn3b/openstack_cache3aGzTU
    clouds:
      devstack:
        auth:
          auth_url: https://identity.uk-1.cloud.global.fujitsu.com/v3
          domain_name: contractid
          password: pass
          project_name: project
          username: user
        private: true
    """
    global OS_AUTH
    with open(config_file) as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)
    auth =config['clouds']['devstack']['auth']
    OS_AUTH['OS_AUTH_URL'] = auth['auth_url']
    OS_AUTH['OS_USER_DOMAIN_NAME'] = auth['domain_name']
    OS_AUTH['OS_PROJECT_DOMAIN_NAME'] = auth['domain_name']
    OS_AUTH['OS_USERNAME'] = auth['username']
    OS_AUTH['OS_PASSWORD'] = auth['password']
    OS_AUTH['OS_PROJECT_NAME'] = auth['project_name']
    #OS_AUTH['OS_PROJECT_ID'] = auth['']                # not available from AWX
    #OS_AUTH['OS_IDENTITY_API_VERSION'] = auth['']      # not available from AWX
    #OS_AUTH['OS_REGION_NAME'] = auth['']               # not available from AWX

def create_config_from_args():
    global OS_AUTH
    for arg in OS_AUTH.keys():
        value = os.environ.get(arg, None)
        # overwrite OS_AUTH     
        if value != None:   
            OS_AUTH[arg] = value

def get_k5_server_details(token, url, name=None):
    if name == None:
        name='' # blank addition to the url
    session = requests.Session()
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'X-Auth-Token': token }
    url = url + '/servers/detail' + name
    try:
        response = session.request('GET', url, headers=headers)
    except requests.exceptions.RequestException as e:
        print e
        sys.exit(1)
    # we failed to authenticate
    if response.status_code not in (200,):
        print "RESP: HTTP Code:" + str(response.status_code) + " " + str(response.content)
        sys.exit(1)
    resp = response.json()['servers']
    return resp

def get_k5_image_details(token, url):
    session = requests.Session()
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'X-Auth-Token': token }
    url = url + '/images/detail'
    try:
        response = session.request('GET', url, headers=headers)
    except requests.exceptions.RequestException as e:
        print e
        sys.exit(1)
    # we failed to authenticate
    if response.status_code not in (200,):
        print "RESP: HTTP Code:" + str(response.status_code) + " " + str(response.content)
        sys.exit(1)
    resp = response.json()['images']
    return resp

def get_k5_flavor_details(token, url):
    session = requests.Session()
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'X-Auth-Token': token }
    url = url + '/flavors/detail'
    try:
        response = session.request('GET', url, headers=headers)
    except requests.exceptions.RequestException as e:
        print e
        sys.exit(1)
    # we failed to authenticate
    if response.status_code not in (200,):
        print "RESP: HTTP Code:" + str(response.status_code) + " " + str(response.content)
        sys.exit(1)
    resp = response.json()['flavors']
    return resp

def generate_hostvars(servers, flavors, images, internal_ips=False):
   
    for server in servers:

        server_name = server['name']       
 
        hostvars = default_json['_meta']['hostvars']

        hostvars[server_name] = server

        # get flavor name
        flavor_id = server['flavor']['id']
        flavor = next(( x for x in flavors if x['id'] == flavor_id), None)
        if flavor == None:
            flavor_name = "None"
        else:
            flavor_name = flavor['name']
        hostvars[server_name]['k5_flavor'] = flavor_name
        
        # get image name
        try:
            image_id = server['image']['id']
            image = next(( x for x in images if x['id'] == image_id), None)
            if image == None:
                image_name = "None"
            else:
                image_name = image['name']
        except:
            image_name = "None"
        hostvars[server_name]['k5_image'] = image_name

        # get external / floating IP as ansible_ssh_host
        #
        # this may croak if you have dual-homed NICs etc, or at least overwrite the IP you want 
        ansible_ssh_host = ""
        addresses = server['addresses']
        floating = ""
        fixed = ""
        for net in addresses:
            for addr in addresses[net]:
                if addr['OS-EXT-IPS:type'] == 'floating':
                    floating = addr['addr']
                else:
                    fixed = addr['addr']

        if internal_ips:
            ansible_ssh_host = fixed
        else:
            # we try and use the internet public IPs
            if floating != "":
                ansible_ssh_host = floating
            else:
                ansible_ssh_host = fixed  # openstack dynamic inventory does not do this
            
        hostvars[server_name]['ansible_ssh_host'] = ansible_ssh_host

        # add to group

        groups = default_json

        # all
        if 'all' not in groups:
            groups['all'] = []
        groups['all'].append(server_name)

        # availability_zone
        az = 'az_' + server['OS-EXT-AZ:availability_zone']
        if az not in groups:
            groups[az] = []
        groups[az].append(server_name)

        # image
        image_name = 'image_' + image_name # defined above
        if image_name not in groups:
            groups[image_name] = []
        groups[image_name].append(server_name) 

        # hypervisor host
        hyp = 'hypervisor_hostname_' + server['OS-EXT-SRV-ATTR:hypervisor_hostname']
        if hyp not in groups:
            groups[hyp] = []
        groups[hyp].append(server_name)
        
        # keyname
        kn = 'keyname_' + server['key_name'] 
        if kn not in groups:
            groups[kn] = []
        groups[kn].append(server_name) 

        # vm status
        status = 'status_' + server['status'] 
        if status not in groups:
            groups[status] = []
        groups[status].append(server_name) 

        # security groups
        for sg in server['security_groups']:
            sg_name='sg_' + sg['name']
            if sg_name not in groups:
                groups[sg_name] = []
            groups[sg_name].append(server_name)

        # metadata - does 'groups' exist as a list
        if 'groups' in server['metadata'].keys():
            grps = server['metadata']['groups']
            if type(grps) is list:
                for g_name in grps:
                    if g_name not in groups:
                        groups[g_name] = []
                    groups[g_name].append(server_name)

        for md in server['metadata']:
            md_name='md_'+md # k only
            val=md_name+'_'+server['metadata'][md] # k,v
            if md_name not in groups:
                groups[md_name] = []
            groups[md_name].append(server_name)
            if val not in groups:
                groups[val] = []
            groups[val].append(server_name)



    print json.dumps(default_json)

    #pp.pprint( default_json )

def list_servers(name=None,internal_ips=False):

    # read in the os config file if available
    OS_CLIENT_CONFIG_FILE = os.environ.get('OS_CLIENT_CONFIG_FILE', None)
    if OS_CLIENT_CONFIG_FILE != None:
        create_config_from_config(OS_CLIENT_CONFIG_FILE)

    # now read ENV VARS to overwrite the Ansible openstack.yaml
    create_config_from_args()

    #pp.pprint(OS_AUTH)

    token, endpoints = get_regional_token()

    # get compute endpoint url
    compute_ep = next(( x for x in endpoints if x['name'] == 'compute'), None)
    #pp.pprint(compute_ep)
    compute_url = compute_ep['endpoints'][0]['url']

    # get servers for this project
    servers = get_k5_server_details(token, compute_url, name)
    #pp.pprint(servers)

    if len(servers) >0:
        flavors = get_k5_flavor_details(token, compute_url)
        #pp.pprint(flavors)
        images = get_k5_image_details(token, compute_url)
        #pp.pprint(images)

    generate_hostvars(servers, flavors, images,internal_ips)



if __name__ == "__main__":

    pp = pprint.PrettyPrinter(indent=2)

    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action="store_true") # make list a variable and give it a boolean True
    parser.add_argument('--host', type=str)
    args = parser.parse_args()

    # check if ENVVAR is available to only list internal IPs
    internal_ips = bool(os.getenv('K5_INTERNAL_IPS'))

    if args.list:
        list_servers(internal_ips=internal_ips)

    if args.host:
        url_args = '?name=' + str(args.host)
        list_servers(internal_ips=internal_ips,name=url_args)

