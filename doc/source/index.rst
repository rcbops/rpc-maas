==================
RPC-MaaS Playbooks
==================

.. toctree::
   :maxdepth: 2


:tags: openstack, nova, cloud, ansible
:category: \*nix

These playbooks allow deployers to monitor clouds using Rackspace Monitoring
as a Service. The playbooks can be used with OpenStack-Ansible or on their
own using Ansible static inventory.

Default variables
~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/main.yml
   :language: yaml
   :start-after: under the License.


Agent playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-agent.yml
   :language: yaml
   :start-after: under the License.

Container playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-container.yml
   :language: yaml
   :start-after: under the License.

Host playbook variables
~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-host.yml
   :language: yaml
   :start-after: under the License.

Infra playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-infra.yml
   :language: yaml
   :start-after: under the License.

OpenStack playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-openstack.yml
   :language: yaml
   :start-after: under the License.


Example Usage
#############

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
~~~~~~~~~~~~~~~~~~~~~~~~~

After deployment you can run a local validation playbook to ensure that
everything is working as expected which can be done with static inventory
as well as within an OpenStack-Ansible deployment.

With OpenStack-Ansible
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Set the inventory path so Ansible knows how to do an inventory run.
    export ANSIBLE_INVENTORY="/opt/openstack-ansible/playbooks/inventory"

    # Run the test playbook
    openstack-ansible playbooks/maas-verify.yml


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


With Static Inventory
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Run the test playbook
    ansible-playbook -i inventory playbooks/maas-verify.yml


Tags
~~~~

This role supports several high level tags: ``maas``, ``maas-agent``,
``maas-ceph``, ``maas-container``, ``maas-host``, ``maas-infra``,
``maas-openstack``. Within each group a tag exists for a specific playbook.
This gives the deployer the ability to control orchestration even when
running the general ``site.yml`` playbook.


Paybook Specific Notes
######################

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


Building Static Inventory
#########################


Mandatory Sections
^^^^^^^^^^^^^^^^^^

To begin you likely will want to define all of your physical hosts within the
"all" section.

.. code-block:: ini

    [all]
    localhost ansible_connection=local
    infra1 ansible_host=10.0.0.1
    openstack1 ansible_host=10.0.0.2
    swift1 ansible_host=10.0.0.3
    hap1 ansible_host=10.0.0.4
    ceph1 ansible_host=10.0.0.5


With all of your entries defined you'll want to specify all of your *physical*
host machines under the "hosts" section.

.. code-block:: ini

    [hosts]
    localhost
    ceph1


Optional Sections
^^^^^^^^^^^^^^^^^

If you have ``containers``, these entries will be added to the "all_containers"
section.

.. code-block:: ini

    [all_containers]
    infra1
    openstack1
    swift1
    hap1


Infrastructure Sections
~~~~~~~~~~~~~~~~~~~~~~~

If you have node(s) running ``MariaDB with Galera``, add the node(s) into the
"galera" section

.. code-block:: ini

    [galera]
    infra1

    [galera_all:children]
    galera


If you have node(s) running ``haproxy``, add the node(s) into the "haproxy"
section

.. code-block:: ini

    [haproxy]
    hap1

    [haproxy_all:children]
    haproxy


If you have node(s) running ``memcached``, add the node(s) into the
"memcached" section

.. code-block:: ini

    [memcached]
    infra1

    [memcached_all:children]
    memcached


If you have node(s) running ``rabbitmq``, add the node(s) into the
"rabbitmq" section

.. code-block:: ini

    [rabbitmq]
    infra1

    [rabbitmq_all:children]
    rabbitmq


If you have node(s) running ``ceph``, add the node(s) into the "ceph"
section

.. code-block:: ini

    [mons]
    ceph1

    [osds]
    ceph1

    [ceph_all:children]
    mons
    osds


If you have node(s) running ``elasticsearch``, add the node(s) into the
"elasticsearch" section

.. code-block:: ini

    [elasticsearch]
    infra1

    [elasticsearch_all:children]
    elasticsearch


If you have node(s) running ``rsyslog``, add the node(s) into the
"rsyslog" section

.. code-block:: ini

    [rsyslog_all:children]
    hosts
    all_containers


If you want to do an ``ssl`` check on your Load balancers, add the
node(s) into the "utility" section

.. code-block:: ini

    [utility]
    infra1

    [utility_all:children]
    utility


OpenStack Sections
~~~~~~~~~~~~~~~~~~

Within the OpenStack portion of the static inventory, not all sections
are required for every service. You can chose to omit certain sections
if you do not want to monitor the components covered by the section.

If you have node(s) running ``cinder``, add the node(s) into the "cinder"
section.

.. code-block:: ini

    [cinder_api]
    openstack1

    [cinder_scheduler]
    openstack1

    [cinder_backup]
    openstack1

    [cinder_volume]
    openstack1

    [cinder_all:children]
    cinder_api
    cinder_scheduler
    cinder_backup
    cinder_volume


If you have node(s) running ``glance``, add the node(s) into the "glance"
section.

.. code-block:: ini

    [glance_api]
    openstack1

    [glance_registry]
    openstack1

    [glance_all:children]
    glance_api
    glance_registry


If you have node(s) running ``heat``, add the node(s) into the "heat" section.

.. code-block:: ini

    [heat_api]
    openstack1

    [heat_engine]
    openstack1

    [heat_api_cfn]
    openstack1

    [heat_api_cloudwatch]
    openstack1

    [heat_engine_container]
    openstack1

    [heat_apis_container]
    openstack1

    [heat_all:children]
    heat_api
    heat_engine
    heat_api_cfn
    heat_api_cloudwatch
    heat_engine_container
    heat_apis_container


If you have node(s) running ``horizon``, add the node(s) into the "horizon"
section.

.. code-block:: ini

    [horizon]
    openstack1

    [horizon:children]
    horizon


If you have node(s) running ``keystone``, add the node(s) into the "keystone"
section.

.. code-block:: ini

    [keystone]
    openstack1

    [keystone:children]
    keystone


If you have node(s) running ``magnum``, add the node(s) into the "magnum"
section.

.. code-block:: ini

    [magnum]
    openstack1

    [magnum:children]
    magnum


If you have node(s) running ``neutron``, add the node(s) into the "neutron"
section.

.. code-block:: ini

    [neutron_agent]
    openstack1

    [neutron_dhcp_agent]
    openstack1

    [neutron_linuxbridge_agent]
    openstack1

    [neutron_openvswitch_agent]

    [neutron_metering_agent]
    openstack1

    [neutron_l3_agent]
    openstack1

    [neutron_lbaas_agent]
    openstack1

    [neutron_metadata_agent]
    openstack1

    [neutron_server]
    openstack1

    [neutron_all:children]
    neutron_agent
    neutron_dhcp_agent
    neutron_linuxbridge_agent
    neutron_openvswitch_agent
    neutron_metering_agent
    neutron_l3_agent
    neutron_lbaas_agent
    neutron_metadata_agent
    neutron_server


If you have node(s) running ``nova``, add the node(s) into the "nova" section.

.. code-block:: ini

    [nova_api_metadata]
    openstack1

    [nova_api_os_compute]
    openstack1

    [nova_cert]
    openstack1

    [nova_compute]
    openstack1

    [nova_conductor]
    openstack1

    [nova_console]
    openstack1

    [nova_scheduler]
    openstack1

    [nova_api_placement]
    openstack1

    [nova_all:children]
    nova_api_metadata
    nova_api_os_compute
    nova_cert
    nova_compute
    nova_conductor
    nova_console
    nova_scheduler
    nova_api_placement


If you have node(s) running ``swift``, add the node(s) into the "swift"
section.

.. code-block:: ini

    [swift_hosts]
    swift1

    [swift_proxy]
    swift1

    [swift_acc]
    swift1

    [swift_cont]
    swift1

    [swift_obj]
    swift1

    [swift_all:children]
    swift_acc
    swift_proxy
    swift_cont
    swift_obj
