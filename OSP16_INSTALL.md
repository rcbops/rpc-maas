# rpc-maas OSP16 install docs

## Overview

A separate 'osp16' branch was created to support some of the following changes:
* python3 support
* RHEL8 system dependancies
* newer rally version
* OSP16 inventory layout changes

I removed the need for MTC with a quick shell script that sets up /root/ansible_venv used for the installation.  Apart from the removal of MTC the internal documentation can still be used for everything else. 
* [internal monitoring docs](https://pages.github.rackspace.com/rpc-internal/docs-rpc/rpc-monitoring-internal/index.html)

## Download rpc-maas

```
git clone https://github.com/rcbops/rpc-maas /opt/rpc-maas
cd /opt/rpc-maas/
git checkout osp16
```

## Setting up the installer venv

Ran as root on the director vm.
```
cd /opt/rpc-maas/
./scripts/osp16-prep.sh
```

## Creating rackspace monitoring entities and agent tokens.

According to the docs the rackspace-monitoring-agent installation and entity creation is handled by the rackspace cloud engineers.  It doesn't cover this in detail, so I'm assuiming our deployment guys have the steps down for that.  Before continuing on the following must be completed.
* Entity and agent token creation.
* Installation of the rackspace-monitoring-agent. (redhat 8 packages are available)
* Configuration of the rackspace-monitoring-agent with the entity and agent token.

See the docs for details on a [decoupled environment](https://pages.github.rackspace.com/rpc-internal/docs-rpc/rpc-monitoring-internal/monitoring-impl/monitoring-internal.html#id5) for more details.

## Generating an auth-token

This may already be obtained from pitchfork or whatever the rackspace cloud enginners used to set up the entities.  If you have a pubcloud username and api key, you can use the following gating test script to pull the auth token. The values for the url and auth token can be found in /root/maas-vars.rc after.

```
/root/ansible_venv/bin/python3 tests/maasutils.py --username <pubcloud_username> --api-key <pubcloud_api_key> get_token_url
Credentials file written to "/root/maas-vars.rc"
```

## Creating the rpc-maas config file

This is the primary config file used for the rpc-maas install.  It will vary depending on the environment. Follow the docs to complete the config.
* [Configuring Overrides](https://pages.github.rackspace.com/rpc-internal/docs-rpc/rpc-monitoring-internal/monitoring-impl/monitoring-internal.html#step-2-configuring-overrides) 

```
vi /home/stack/user_maas_variables.yml
```

* Example:
```
# MaaS v2 overrides
maas_api_url: "https://monitoring.api.rackspacecloud.com/v1.0/<tenant id>"
maas_auth_token: "<taken from the /root/maas-vars.rc if using the test script>"

# The entityLabel should based on the 'maas_fqdn_extension', as follows:
# entityLabel == 'undercloudlab1.phobos.rpc.rackspace.com'
# Refer to the naming convention documentation section for additional details
#
maas_fqdn_extension: "lab1.phobos.rpc.rackspace.com"

# Define a Unique Environment ID
# If multiple clouds exist on an account, each should have a different value
# This is also used to generate objects for private pollers if used.
#
maas_env_identifier: "dciosp16test"

# Enable this with  to install and configure private
# pollers for ping and lb checks.
# - 'maas_env_identifier' is also required for the private poller zone object
#maas_private_monitoring_enabled: true

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

maas_rabbitmq_password: "<some random pass>"
maas_swift_accesscheck_password: "<some random pass>"
```

## Run the install
```
cd /opt/rpc-maas
. /root/ansible_venv/bin/activate
ansible-playbook -i /opt/rpc-maas/inventory/rpcr_dynamic_inventory.py \
                 -e @/home/stack/user_maas_variables.yml \
                 -f 75 playbooks/site.yml
deactivate

```

## Verify the install
```
cd /opt/rpc-maas
. /root/ansible_venv/bin/activate
ansible-playbook -i /opt/rpc-maas/inventory/rpcr_dynamic_inventory.py \
                 -e @/home/stack/user_maas_variables.yml \
                 -f 75 playbooks/maas-verify.yml
deactivate
```


## Rally performance checks(if required by customer)

* Update the config to enable rally
```
vi /home/stack/user_maas_variables.yml
```
```
...
maas_rally_enabled: true
maas_rally_users_password: "<some random pass>"
maas_rally_galera_password: "<some random pass>"
maas_rally_check_overrides:
  cinder:
    enabled: false
  glance:
    enabled: true
  keystone:
    enabled: true
  neutron_ports:
    enabled: true
  neutron_secgroups:
    enabled: true
  nova:
    enabled: false
  nova_cinder:
    enabled: false
  swift:
    enabled: true
    extra_user_roles:
      - "swiftoperator"
```

* Run the rally install
```
cd /opt/rpc-maas
. /home/stack/overcloudrc
. /root/ansible_venv/bin/activate
ansible-playbook -i /opt/rpc-maas/inventory/rpcr_dynamic_inventory.py \
                 -e @/home/stack/user_maas_variables.yml  \
                 -e "keystone_auth_admin_password=${OS_PASSWORD}" \
                 -f 75 playbooks/maas-openstack-rally.yml 
deactivate
```

