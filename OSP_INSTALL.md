
# rpc-maas OSP install docs

## Download rpc-maas

```
git clone https://github.com/rcbops/rpc-maas /opt/rpc-maas
cd /opt/rpc-maas/
```

## Setting up the installer venv

Ran as root on the director vm.
```
cd /opt/rpc-maas/
./scripts/prepare.sh
```

## Creating rackspace monitoring entities and agent tokens.

According to the docs the rackspace-monitoring-agent installation and entity creation is handled by the rackspace cloud engineers. Before continuing on the following must be completed.

* Entity and agent token creation.

## Update the rpc-maas config file

This is the primary config file used for the rpc-maas install.  It will vary depending on the environment. Follow the docs to complete the config.
* [Configuring Overrides](https://pages.github.rackspace.com/rpc-internal/docs-rpc/master/rpc-monitoring-internal/monitoring-impl/monitoring-internal.html#step-2-configuring-overrides) 

```
vi /opt/rpc-maas/user_maas_variables.yml
```

* Example:
```
# MaaS v2 overrides
maas_auth_method: token
maas_api_url: https://monitoring.api.rackspacecloud.com/v1.0/hybrid:<account>
maas_auth_token: <maas_auth_token>
maas_agent_token: <maas_agent_token>
#maas_notification_plan: npManaged
maas_notification_plan: npTechnicalContactsEmail
maas_notification_plan_override: {}
# The entityLabel should based on the 'maas_fqdn_extension', as follows:
# entityLabel == '{{ inventory_hostname }}{{ maas_fqdn_extension }}'
# Refer to the naming convention documentation section for additional details
#
maas_fqdn_extension: ""

# Define a Unique Environment ID
# If multiple clouds exist on an account, each should have a different value
#
maas_env_identifier: "lab-tnd1"

# Identify data center requirements for PNM and hardware monitoring
#  true = Rackspace DC (RDC) or OpenStack Everywhere deployments
# false = Customer DC (CDC)
#
maas_raxdc: true

# Release-specific exclusions are now handled dynamically. These
# overrides will likely remain empty. These are included for
# compatibility to remove any remnant host_vars that may have
# existed in the inventory.
maas_excluded_checks: []
maas_excluded_alarms: []

maas_rabbitmq_password: "W9XAvUdM9bPEexa"
maas_swift_accesscheck_password: "7eEmTknw2zyLf8H"

# Set the OSA/RPCO working directories ONLY if you use non-standard
# directories. If these locations differ from the list below, update and
# uncomment accordingly.
maas_product_dir: /opt/rpc-maas
maas_product_osa_dir: /opt/rpc-maas

# Set the product type. Valid options are: rpco, osa, or ceph.
# Only set 'osa' if there is no corresponding rpco directory.
maas_env_product: rpco

# Allow operations that make use of the MaaS API
maas_use_api: true

# Enable remote lb_api_checks
maas_remote_check: true

# Enable Dell/HP Hardware monitoring checks
maas_host_check: true

# Switch the MaaS scheme to https
maas_scheme: https

# Disable if non-transparent web proxy is preventing raxmon SSL verification
maas_raxmon_ssl_verify: true

# Set overrides for check period/timeout
maas_check_period_override:
  disk_utilisation: 900
  hp-check: 300
  nova_api_local_check: 120
  neutron_api_local_check: 120
maas_check_timeout_override:
  disk_utilisation: 899
  hp-check: 299
  nova_api_local_check: 119
  neutron_api_local_check: 119

maas_rabbitmq_user: maas

local_suffix: ".localdomain"
ansible_nodename: "{{inventory_hostname}}{{local_suffix}}"

#neutron_plugin_type: ovn
horizon_service_protocol: 'http'
horizon_service_port: '80'

## OSP17 defaults
undercloud_provisioning_interface: "br_ctlplane"
ansible_user: tripleo-admin
physical_host: "{{ hostvars[inventory_hostname]['ansible_'+provisioning_interface]['ipv4']['address'] }}"
container_address: "{{ internal_api_ip | default(physical_host) }}"

## OSP17
deploy_osp: true
maas_stackrc: /home/stack/lab-tnd1rc
overcloud_stack: "lab-tnd1"
overcloud_provisioning_interface: "eno1"
```

## Run the install
```
cd /opt/rpc-maas
. /root/ansible_venv/bin/activate
ansible-playbook -i /opt/rpc-maas/inventory/inventory.py  \
                 -i /home/stack/tripleo-deploy/undercloud/tripleo-ansible-inventory.yaml \
                 -i /home/stack/overcloud-deploy/<stack>/tripleo-ansible-inventory.yaml \
                 -e @/opt/rpc-maas/user_maas_variables.yml \
                 -f 75 playbooks/site.yml \
                 --ssh-common-args='-o StrictHostKeyChecking=no' \
                 --private-key  /home/stack/.ssh/id_rsa
deactivate
```
