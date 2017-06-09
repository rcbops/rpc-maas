===============
Usage Reference
===============

These playbooks can be used with OpenStack-Ansible or with stand
alone inventory. The following sections cover examples of how
the playbooks could be used.


Example usage with Ansible static Inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    ansible-playbook -i tests/inventory playbooks/site.yml


Example usage with OpenStack-Ansible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    export ANSIBLE_INVENTORY="/opt/openstack-ansible/playbooks/inventory"
    openstack-ansible playbooks/site.yml


Validating the deployment
-------------------------

After deployment you can run a local validation playbook to ensure that
everything is working as expected which can be done with static inventory
as well as within an OpenStack-Ansible deployment.


Running with OpenStack-Ansible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Set the inventory path so Ansible knows how to do an inventory run.
    export ANSIBLE_INVENTORY="/opt/openstack-ansible/playbooks/inventory"

    # Run the test playbook
    openstack-ansible playbooks/maas-verify.yml


Running with Static Inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Run the test playbook
    ansible-playbook -i inventory playbooks/maas-verify.yml


Running with Ansible 1.9 and OpenStack-Ansible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prior to running with Ansible 1.9 with OpenStack-Ansible (using the Mitaka,
Liberty, Kilo) export the Role and Library path prior to running the
playbooks.

.. code-block:: bash

    export ANSIBLE_ROLES_PATH=/opt/openstack-ansible/playbooks/roles
    export ANSIBLE_LIBRARY=/opt/openstack-ansible/playbooks/library


The variable ``ansible_ssh_host`` needs to be set within the
``user_variables.yml`` file.

.. code-block:: bash

    echo 'ansible_host: "{{ ansible_ssh_host }}"' | tee -a /etc/openstack_deploy/user_variables.yml


In order to enable console auth checking set the ``nova_console_type`` and
``nova_console_port`` variables in your ``user_variables.yml`` file.

.. code-block:: bash

    echo 'nova_console_type: spice' | tee -a /etc/openstack_deploy/user_variables.yml
    echo 'nova_console_port: 6082' | tee -a /etc/openstack_deploy/user_variables.yml


Recommended Overrides for specific versions of OpenStack-Ansible
----------------------------------------------------------------

The following sections contain YAML options that should be added to the
``user_variables.yml`` file for a given deployment of OpenStack-Ansible.


Kilo Overrides
~~~~~~~~~~~~~~

.. code-block:: yaml

   # Set overrides for check periods
   maas_check_period_override:
     disk_utilisation: 900

   # Disable the following MaaS alarms
   # Issue: https://github.com/rcbops/u-suk-dev/issues/1081
   maas_excluded_alarms:
     - '^idle_percent_average.*'
     - '^memory_check.*'
     - '^Network receive rate.*'
     - '^Network transmit rate.*'
     - '^percentage_disk_utilisation.*'

   # swift-recon does not have '--time' option in Kilo
   maas_excluded_checks:
     - 'swift_time_sync_check'

   # Ansible 1.9 compatibility
   ansible_host: "{{ ansible_ssh_host }}"


Liberty Overrides
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # Set overrides for check periods
   maas_check_period_override:
     disk_utilisation: 900

   # Disable the following MaaS alarms
   # Issue: https://github.com/rcbops/u-suk-dev/issues/1081
   maas_excluded_alarms:
     - '^idle_percent_average.*'
     - '^memory_check.*'
     - '^Network receive rate.*'
     - '^Network transmit rate.*'
     - '^percentage_disk_utilisation.*'

   # The ELK stack does not use filebeat in this release
   maas_excluded_checks:
     - 'filebeat_process_check'

   # Ansible 1.9 compatibility
   ansible_host: "{{ ansible_ssh_host }}"


Mitaka Overrides
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # Set overrides for check periods
   maas_check_period_override:
     disk_utilisation: 900

   # Disable the following MaaS alarms
   # Issue: https://github.com/rcbops/u-suk-dev/issues/1081
   maas_excluded_alarms:
     - '^idle_percent_average.*'
     - '^memory_check.*'
     - '^Network receive rate.*'
     - '^Network transmit rate.*'
     - '^percentage_disk_utilisation.*'

   maas_excluded_checks: []

   # Ansible 1.9 compatibility
   ansible_host: "{{ ansible_ssh_host }}"


Tags
----

This role supports several high level tags: ``maas``, ``maas-agent``,
``maas-ceph``, ``maas-container``, ``maas-host``, ``maas-infra``,
``maas-openstack``. Within each group a tag exists for a specific playbook.
This gives the deployer the ability to control orchestration even when
running the general ``site.yml`` playbook.


Playbook Specific Notes
-----------------------

Some playbooks have specific variables that must be set for them to work.
These specifics are covered here.

maas-infra-rabbitmq.yml
~~~~~~~~~~~~~~~~~~~~~~~

The ``maas-infra-rabbitmq.yml`` playbook will create a user within the
rabbitmq cluster for the purposes of monitoring. For this to happen a
password must be set in a secrets file somewhere and referenced during the
playbook run. The variable required to be set is ``maas_rabbitmq_password``.

.. code-block:: bash

    # Variable file set
    echo 'maas_rabbitmq_password: secrete' | tee -a /etc/openstack_deploy/user_secrets.yml

    # Example playbook run with variable file.
    ansible-playbook -e @/etc/openstack_deploy/user_secrets.yml /opt/rpc-maas/playbooks/maas-infra-rabbitmq.yml -i inventory


maas-openstack-keystone.yml
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``maas-openstack-keystone.yml`` playbook will create a user within
keystone for the purposes of monitoring. For this to happen a password
must be set in a secrets file somewhere and referenced during the playbook
run. The variable required to be set is ``maas_rabbitmq_password``.

.. code-block:: bash

    # Variable file set
    echo 'maas_keystone_password: secrete' | tee -a /etc/openstack_deploy/user_secrets.yml

    # Example playbook run with variable file.
    ansible-playbook -e @/etc/openstack_deploy/user_secrets.yml /opt/rpc-maas/playbooks/maas-openstack-keystone.yml -i inventory


maas-openstack-swift.yml
~~~~~~~~~~~~~~~~~~~~~~~~

The ``maas-openstack-swift.yml`` playbook will create a user within keystone
for the purposes of monitoring and then upload an index.html object to a
configurable containe within swift. For this to happen a password must be set
in a secrets file somewhere and referenced during the playbook run. The
variable required to be set is ``maas_swift_accesscheck_password``.

.. code-block:: bash

    # Variable file set
    echo 'maas_swift_accesscheck_password: secrete' | tee -a /etc/openstack_deploy/user_secrets.yml

    # Example playbook run with variable file.
    ansible-playbook -e @/etc/openstack_deploy/user_secrets.yml /opt/rpc-maas/playbooks/maas-openstack-swift.yml -i inventory


maas-tigkstack-influxdb.yml
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``maas-tigkstack-influxdb.yml`` playbook will create an influxdb user.
For this to happen a password must be set in a secrets file somewhere and
referenced during the playbook run. The variables required are
``influxdb_db_root_password`` and ``influxdb_db_metric_password``.

.. code-block:: bash

    # Variable file set
    echo 'influxdb_db_root_password: secrete' | tee -a /etc/openstack_deploy/user_secrets.yml
    echo 'influxdb_db_metric_password: secrete'  | tee -a /etc/openstack_deploy/user_secrets.yml

    # Example playbook run with variable file.
    ansible-playbook -e @/etc/openstack_deploy/user_secrets.yml /opt/rpc-maas/playbooks/maas-tigkstack-influxdb.yml -i inventory




Restart flow control
--------------------

When doing an initial deployment of the rpc-maas playbooks it recommended
set the variable  ``maas_restart_independent`` to **false**. This variable
instructs the playbooks to only restart the ``rackspace-monitoring-agent``
once upon the completion of the ``site.yml`` playbook run. If you are
redeploying specific checks, this variable is not needed.

.. code-block:: bash

    ansible-playbook -e "maas_restart_independent=false" /opt/rpc-maas/playbooks/site.yml


Deploying the TIGK Stack
------------------------

If ``the maas-tigkstack-all.yml`` Playbook is run **telegraf** will be
installed throughout the deployment and **influxdb** will be installed
within the *log_host*. Enabling this service will immediately being
collecting metrics within the deployment using the existing MaaS plugins
and enabled checks.


Collecting metrics for time series analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An available plugin can be executed at any time to run all discovered checks
found in ``/etc/rackspace-monitoring-agent.conf.d``. The existing MaaS plugins
will be executed having the output format converted to telegraf line format.
This is useful when storing local checks in a time series database like
influxdb and is part of the normal TIGK Stack deployment and **telegraf**
agent configuration.


To run the plugin execute the following:

.. code-block:: bash

    /openstack/venvs/maas-${VERSION_NUM}/bin/python /usr/lib/rackspace-monitoring-agent/plugins/maas_telegraf_format.py


Setting the job reference
~~~~~~~~~~~~~~~~~~~~~~~~~

When deploying the TIGK Stack you can set the job reference variable to create
a tag on all metrics collected for the specific job. The variable setting is
``maas_job_reference`` which has a default of **testing**. Setting this job
variable will provide the ability to select and search through aggregated
metrics using a simple where clause, example:

.. code-block:: sql

    use telegraf
    select * from nova_api_metadata where job_reference='testing'


This simple query will select everything from the **nova_api_metadata** metric
where the job reference tag is equal to the string "testing".
