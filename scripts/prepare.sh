#!/bin/bash

egrep -i 'Centos|Red Hat' /etc/redhat-release 2>/dev/null && isRH=1

# Install some dependancies
if [ $isRH ]; then
    echo "Notes:
    - Make sure OSP repositories are enabled on all the nodes.
    - Please read the documentation and update /opt/rpc-maas/user_maas_variables.yml config file and set up any entities and agents as needed.
    "

    # Install some dependancies
    rpm -qi python3-pip > /dev/null
    if [ $? != 0 ]; then
        dnf -y install python3-pip
    fi
else
  apt install -y python3-pip
fi

# Create the virtual environment
if [ ! -d /root/ansible_venv ]; then

    # Set up the python virtual env
    python3 -m venv --system-site-packages /root/ansible_venv

fi

# Install required packages
. /root/ansible_venv/bin/activate
pip install -r /opt/rpc-maas/requirements.txt
deactivate

# Generate a token(non core testing when we have the vars set)
if [[ "$PUBCLOUD_USERNAME" != "" ]] && [[ "$PUBCLOUD_API_KEY" != "" ]] && [[ "$PUBCLOUD_TENANT_ID" != "" ]]; then
    . /root/ansible_venv/bin/activate
    ./tests/maasutils.py \
        --username "${PUBCLOUD_USERNAME}" \
        --api-key "${PUBCLOUD_API_KEY}" \
        get_token_url
    deactivate

    # Update the token if vars file exists
    if [ -e /home/stack/user_maas_variables.yml ]; then
        echo "Refreshing the maas_auth_token in /home/stack/user_maas_variables.yml"
        . /root/maas-vars.rc
        sed -i -e "s/^maas_auth_token:.*/maas_auth_token: \"${MAAS_AUTH_TOKEN}\"/g" /home/stack/user_maas_variables.yml
    fi
fi

echo
echo "Example Playbook Usage Post Configuration:
cd /opt/rpc-maas/
. /root/ansible_venv/bin/activate"
if [ $isRH ]; then
    echo "ansible-playbook -i /opt/rpc-maas/inventory/inventory.py  -i /home/stack/tripleo-deploy/undercloud/tripleo-ansible-inventory.yaml -i /home/stack/overcloud-deploy/<stack>/tripleo-ansible-inventory.yaml -e @/opt/rpc-maas/user_maas_variables.yml -f 75 playbooks/site.yml --ssh-common-args='-o StrictHostKeyChecking=no' --private-key  /home/stack/.ssh/id_rsa"
else
  echo ". /usr/local/bin/openstack-ansible.rc"
  echo "# When present add the Ceph inventory to update the maas checks on"
  echo "# the ceph nodes"
  echo 'export ANSIBLE_INVENTORY="$ANSIBLE_INVENTORY,/tmp/inventory-ceph.ini"'
  echo ""
  echo "openstack-ansible playbooks/site.yml"
fi

echo "deactivate"
echo
