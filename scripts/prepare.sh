#!/bin/bash

egrep -i 'Centos|RedHat' /etc/redhat-release 2>/dev/null && isRH=1

# Install some dependancies
if [ $isRH ]; then
  rpm -qi python3-pip python3-virtualenv > /dev/null
  test $? -ne 0 && dnf -y install python3-pip python3-virtualenv

  # Update the python alternatives if needed
  if [ ! -e /usr/bin/python ]; then
      alternatives --set python /usr/bin/python3
  fi
else
  apt install -y python3-pip virtualenv
fi

# Create the virtual environment
if [ ! -d /root/ansible_venv ] || [ ! -f /root/ansible_venv/bin/python3 ]; then
    # Set up the python virtual env
    rm -rf /root/ansible_venv
    virtualenv -p /usr/bin/python3 /root/ansible_venv --system-site-packages
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

# Bomb if the /home/stack/user_maas_variables.yml doesn't exist.
if [ ! -e /home/stack/user_maas_variables.yml ]; then
    echo
    echo "Please read the documentation and create the /home/stack/user_maas_variables.yml config file and set up any entities and agents as needed."
    echo
fi

echo
echo "Example Playbook Usage Post Configuration:
cd /opt/rpc-maas/
. /root/ansible_venv/bin/activate"
if [ $isRH ]; then
  echo "ansible-playbook -i /opt/rpc-maas/inventory/rpcr_dynamic_inventory.py -e @/home/stack/user_maas_variables.yml  playbooks/site.yml"
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
