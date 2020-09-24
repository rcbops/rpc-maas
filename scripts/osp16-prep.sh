#!/bin/bash

# Install some dependancies
rpm -qi python3-pip python3-virtualenv > /dev/null
if [ $? != 0 ]; then
    dnf -y install python3-pip python3-virtualenv
fi

# Update the python alternatives if needed
if [ ! -e /usr/bin/python ]; then
    alternatives --set python /usr/bin/python3
fi

# Create the virtual environment
if [ ! -d /root/ansible_venv ]; then

    # Set up the python virtual env
    virtualenv-3 /root/ansible_venv --system-site-packages

fi

# Install required packages
. /root/ansible_venv/bin/activate
pip install -r ./osp16-requirements.txt
deactivate

# Generate a token(non core testing when we have the vars set)
if [[ "$PUBCLOUD_USERNAME" != "" ]] && [[ "$PUBCLOUD_API_KEY" != "" ]] && [[ "$PUBCLOUD_TENANT_ID" != "" ]]; then
    . /root/ansible_venv/bin/activate
    ./tests/maasutils.py \
        --username "${PUBCLOUD_USERNAME}" \
        --api-key "${PUBCLOUD_API_KEY}" \
        get_token_url
    deactivate
fi

# Bomb if the /home/stack/user_maas_variables.yml doesn't exist.
if [ ! -e /home/stack/user_maas_variables.yml ]; then
    echo "Please read the documentation and create the /home/stack/user_maas_variables.yml config file and set up any entities and agents as needed."
fi

echo "Example Playbook Usage Post Configuration:
cd /opt/rpc-maas/
. /root/ansible_venv/bin/activate
ansible-playbook -i /opt/rpc-maas/inventory/rpcr_dynamic_inventory.py -e @/home/stack/user_maas_variables.yml  playbooks/site.yml
deactivate
"
