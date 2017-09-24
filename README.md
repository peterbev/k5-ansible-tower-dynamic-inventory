# k5-ansible-tower-dynamic-inventory

K5 expects the project id to be defined when creating a authorisation token.
Thus this script also requires this.

You can add an environment variable OS_PROJECT_ID=000000000000000000 to the custom inventory script in yaml
```
OS_PROJECT_ID: '000000000000000000000'
```

The rest of the authentication details are either provided by addtional environment variables (not recommended as you need to provide your password)  or by using the OpenStack Credentials.

##OS_CLIENT_CONFIG_FILE
OS_CLIENT_CONFIG_FILE environment variable is provided by Ansible Towwe which points to a temporary file that contains the Cloud details.

