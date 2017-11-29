#!/bin/bash


# Account information.
export DOMAIN_NAME=$OS_USER_DOMAIN_NAME
export TENANT_ID=$OS_PROJECT_ID
export PROJECT_ID=$TENANT_ID
export USER_NAME=$OS_USERNAME
export USER_PW=$OS_PASSWORD


# Endpoint shortcut. echo "EP initial setup."
export TOKEN=https://identity.uk-1.cloud.global.fujitsu.com
export IDENTITY=$TOKEN
export NETWORK=https://networking.uk-1.cloud.global.fujitsu.com
export COMPUTE=https://compute.uk-1.cloud.global.fujitsu.com
export CEILOMETER=https://telemetry.uk-1.cloud.global.fujitsu.com
export TELEMETRY=$CEILOMETER
export DB=https://database.uk-1.cloud.global.fujitsu.com
export BLOCKSTORAGE=https://blockstorage.uk-1.cloud.global.fujitsu.com
export HOST_BLOCKSTORAGEV2=$BLOCKSTORAGE
export OBJECTSTORAGE=https://objectstorage.uk-1.cloud.global.fujitsu.com
export ORCHESTRATION=https://orchestration.uk-1.cloud.global.fujitsu.com
export ELB=https://loadbalancing.uk-1.cloud.global.fujitsu.com
export AUTOSCALE=https://autoscale.uk-1.cloud.global.fujitsu.com
export IMAGE=https://image.uk-1.cloud.global.fujitsu.com
export MAILSERVICE=https://mail.uk-1.cloud.global.fujitsu.com
export NETWORK_EX=https://networking-ex.uk-1.cloud.global.fujitsu.com
export DNS=https://dns.cloud.global.fujitsu.com
export VMIMPORT=https://vmimport.uk-1.cloud.global.fujitsu.com/v1/imageimport



echo "Authenticating... $DOMAIN_NAME $PROJECT_ID $USER_NAME "

export OS_AUTH_TOKEN=`curl -k -X POST -si $TOKEN/v3/auth/tokens -H "Content-Type:application/json" -H "Accept:application/json" -d '{"auth":{"identity":{"methods":["password"],"password":{"user":{"domain":{"name":"'$DOMAIN_NAME'"}, "name":"'$USER_NAME'", "password": "'"$USER_PW"'"}}}, "scope": { "project": {"id":"'$PROJECT_ID'"}}}}' | awk '/X-Subject-Token/ {print $2}'`

#'"
if [ "$OS_AUTH_TOKEN" == "" ] ; then
        echo "did not authenticate"
        exit 1
fi


read -d '' query_json <<"EOF"
{
                "metadata": {
			"groups": "NickCross, my_group, cool_app",
			"servertype": "awx-all-in-one"
		}
}
EOF

echo $query_json | jq . 

SERVER_ID=$1

if [ "$SERVER_ID" == "" ] ; then
	echo "No server id provided"
	exit 1
fi

curl -si "${COMPUTE}/v2/${TENANT_ID}/servers/${SERVER_ID}/metadata" \
        -X POST \
        -H "X-Auth-Token: $OS_AUTH_TOKEN" \
        -H "Content-Type:application/json" \
        -H "Accept:application/json" \
        -d "$query_json" 

echo ""
