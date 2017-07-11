=========================
Static Inventory Overview
=========================

Mandatory Sections
------------------

all
~~~

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


hosts
~~~~~

With all of your entries defined you'll want to specify all of your *physical*
host machines under the "hosts" section.

.. code-block:: ini

    [hosts]
    localhost
    ceph1


Optional Sections
-----------------

all_containers
~~~~~~~~~~~~~~

If you have ``containers``, these entries will be added to the "all_containers"
section.

.. code-block:: ini

    [all_containers]
    infra1
    openstack1
    swift1
    hap1


Infrastructure Sections
-----------------------

galera_all
~~~~~~~~~~

If you have node(s) running ``MariaDB with Galera``, add the node(s) into the
"galera" section

.. code-block:: ini

    [galera]
    infra1

    [galera_all:children]
    galera


haproxy_all
~~~~~~~~~~~

If you have node(s) running ``haproxy``, add the node(s) into the "haproxy"
section

.. code-block:: ini

    [haproxy]
    hap1

    [haproxy_all:children]
    haproxy


memcached_all
~~~~~~~~~~~~~

If you have node(s) running ``memcached``, add the node(s) into the
"memcached" section

.. code-block:: ini

    [memcached]
    infra1

    [memcached_all:children]
    memcached


rabbitmq_all
~~~~~~~~~~~~

If you have node(s) running ``rabbitmq``, add the node(s) into the
"rabbitmq" section

.. code-block:: ini

    [rabbitmq]
    infra1

    [rabbitmq_all:children]
    rabbitmq


ceph_all
~~~~~~~~

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


elasticsearch_all
~~~~~~~~~~~~~~~~~

If you have node(s) running ``elasticsearch``, add the node(s) into the
"elasticsearch" section

.. code-block:: ini

    [elasticsearch]
    infra1

    [elasticsearch_all:children]
    elasticsearch


rsyslog_all
~~~~~~~~~~~

If you have node(s) running ``rsyslog``, add the node(s) into the
"rsyslog" section

.. code-block:: ini

    [rsyslog_all:children]
    hosts
    all_containers


utility_all
~~~~~~~~~~~

If you want to do an ``ssl`` check on your Load balancers, add the
node(s) into the "utility" section

.. code-block:: ini

    [utility]
    infra1

    [utility_all:children]
    utility


OpenStack Sections
------------------

cinder_all
~~~~~~~~~~

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


glance_all
~~~~~~~~~~

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


heat_all
~~~~~~~~

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


horizon_all
~~~~~~~~~~~

If you have node(s) running ``horizon``, add the node(s) into the "horizon"
section.

.. code-block:: ini

    [horizon]
    openstack1

    [horizon_all:children]
    horizon


keystone_all
~~~~~~~~~~~~

If you have node(s) running ``keystone``, add the node(s) into the "keystone"
section.

.. code-block:: ini

    [keystone]
    openstack1

    [keystone_all:children]
    keystone


magnum_all
~~~~~~~~~~

If you have node(s) running ``magnum``, add the node(s) into the "magnum"
section.

.. code-block:: ini

    [magnum]
    openstack1

    [magnum_all:children]
    magnum


neutron_all
~~~~~~~~~~~

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


nova_all
~~~~~~~~

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


swift_all
~~~~~~~~~

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


influx_hosts
~~~~~~~~~~~~

If you have node(s) running ``influx``, add the node(s) into the "influx_hosts"
section.

.. code-block:: ini

    [influx_hosts]
    influx1

    [influx_all:children]
    influx_hosts
