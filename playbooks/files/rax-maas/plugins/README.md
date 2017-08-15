**Please use the following rules when creating rcbops MaaS plugins:**

1. Import errors result in an error status.
2. Inability to access a dependent service (such as keystone) also result in an error status.
3. Not able to obtain a client or not able to connect to the API endpoint returns status OK, and the problem is reported in the metrics as the API being down.  No further metrics are sent at this point (including a response time).
4. Unexpected exceptions triggered during the run cause an error status, with the text of the exception in the message.
5. Response times are reported as uint32 in milliseconds.

A discussion of these rules can be found in <https://github.com/rcbops/rcbops-maas/pull/43>.


### SUPPORTING LIBRARIES

#### maas_common.py  

Contains many helper functions that the various plugins use to perform keystone authentication, write metrics consistently, handle errors consistently etc.  For keystone auth, it expects the presence of a /root/openrc-maas that contains credentials for a keystone user that you have created specifically for the purposes of monitoring.
The contents of this file would look something like this:

    # COMMON OPENSTACK ENVS
    export OS_USERNAME=maas-user
    export OS_PASSWORD=mypassword
    export OS_TENANT_NAME=maas-tenant
    export OS_AUTH_URL=http://1.2.3.4:5000/v2.0
    export OS_NO_CACHE=1

### LOCAL API CHECKS

***
#### nova_api_local_check.py

##### Description:
Polls a nova API living on the specified IP. Checks to see if the API is up, and then also gathers a list of metrics to return
##### Mandatory Arguments:
IP address of service to test
##### Example Output:

    status okay
    metric nova_api_local_status uint32 1
    metric nova_api_local_response_time double 186.774 ms
    metric nova_instances_in_state_ACTIVE uint32 2 instances
    metric nova_instances_in_state_STOPPED uint32 0 instances
    metric nova_instances_in_state_ERROR uint32 0 instances

***
#### nova_cloud_stats.py

##### Description:
Polls a nova API living on the specified IP. Checks statistics at the 'whole cloud' level and reports as metrics
##### Mandatory Arguments:
IP address of service to test
##### Example Output:

    status okay
    metric cloud_resource_total_memory uint32 15704 Megabytes
    metric cloud_resource_free_disk_space uint32 310 Gigabytes
    metric cloud_resource_used_memory uint32 4096 Megabytes
    metric cloud_resource_used_disk_space uint32 4 Gigabytes
    metric cloud_resource_free_memory uint32 11608 Megabytes
    metric cloud_resource_hypervisor_count uint32 2 hypervisors
    metric cloud_resource_total_disk_space uint32 314 Gigabytes
    metric cloud_resource_used_vcpus uint32 0 vcpu
    metric cloud_resource_total_vcpus uint32 16 vcpu

***
#### cinder_api_local_check.py

##### Description:
Polls a cinder API living on the specified IP. Checks to see if the API is up, and then also gathers a list of metrics to return--

##### Mandatory Arguments:
IP address of service to test
##### Example Output:

    status okay
    metric cinder_api_local_status uint32 1
    metric cinder_api_local_response_time double 211.968 ms
    metric total_cinder_volumes uint32 2 volumes
    metric cinder_available_volumes uint32 1 volumes
    metric cinder_in-use_volumes uint32 1 volumes
    metric cinder_error_volumes uint32 0 volumes
    metric total_cinder_snapshots uint32 0 snapshots
    metric cinder_available_snaps uint32 0 snapshots
    metric cinder_in-use_snaps uint32 0 snapshots
    metric cinder_error_snaps uint32 0 snapshots

***
#### keystone_api_local_check.py

##### Description:
Polls a keystone API living on the specified IP. Checks to see if the API is up, and then also gathers a list of metrics to return--
##### Mandatory Arguments:
IP address of service to test
##### Example Output:

    status okay
    metric keystone_api_local_status uint32 1
    metric keystone_api_local_response_time double 67.161 ms
    metric keystone_user_count uint32 12 users
    metric keystone_tenant_count uint32 2 tenants

***
#### neutron_api_local_check.py

##### Description:
Polls a neutron API living on the specified IP. Checks to see if the API is up, and then also gathers a list of metrics to return--
##### Mandatory Arguments:
IP address of service to test
##### Example Output:

    status okay
    metric neutron_api_local_status uint32 1
    metric neutron_api_local_response_time double 188.356 ms
    metric neutron_networks uint32 1 networks
    metric neutron_agents uint32 21 agents
    metric neutron_routers uint32 0 routers
    metric neutron_subnets uint32 1 subnets

***
#### glance_api_local_check.py

##### Description:
Polls a glance API living on the specified IP. Checks to see if the API is up, and then also gathers a list of metrics to return--

##### Mandatory Arguments:
IP address of service to test
##### Example Output:

    status okay
    metric glance_api_local_status uint32 1
    metric glance_api_local_response_time double 325.883 ms
    metric glance_active_images uint32 2 images
    metric glance_queued_images uint32 0 images
    metric glance_killed_images uint32 0 images

***
#### heat_api_local_check.py

##### Description:
Polls a (native) heat API living on the specified IP. Checks to see if the API is up, and then also gathers a list of metrics to return--

##### Mandatory Arguments:
IP address of service to test
##### Example Output:

    metric heat_api_local_status uint32 1
    metric heat_api_local_response_time double 22.752 ms

***
#### ironic_api_local_check.py

##### Description:
Polls a (native) ironic API living on the specified IP. Checks to see if the API is up, and then also gathers a list of metrics to return--

##### Mandatory Arguments:
IP address of service to test
##### Example Output:

    status okay
    metric client_success uint32 1
    metric ironic_api_local_status uint32 1
    metric ironic_api_local_response_time double 42.690 ms

***
#### ironic_capacity_check.py

##### Description:
Polls a (native) ironic API living on the specified IP. Gathers the number of total nodes and up nodes (nodes not in maintenance)

##### Mandatory Arguments:
IP address of service to test
##### Example Output:

    status okay
    metric client_success uint32 1
    metric ironic_up_nodes_count uint32 1
    metric ironic_total_nodes_count uint32 1

***
#### magnum_api_local_check.py

##### Description:
Polls a (native) magnum API living on the specified IP. Checks to see if the API is up, and then also gathers a list of metrics to return.

##### Mandatory Arguments:
IP address of service to test
##### Example Output:

    status okay
    metric magnum_api_local_status uint32 1
    metric magnum_api_local_response_time double 48.532 ms

***
#### service_api_local_check.py

##### Mandatory Arguments:
- Name of service to test
- IP address of service to test
- Port of service to test
##### Optional Arguments:
- --path: path to tag on to the end of the url
- --auth: whether to authenticate with keystone before the request
- --ssl: use https or not
- --version: hit a specific version of the api

##### Example Output:

    metric <name>_api_local_status uint32 1
    metric <name>_api_local_response_time double 6.222 ms

***
***

### SERVICE CHECKS

#### nova_service_check.py

##### Description:
polls the nova api and gets a list of all nova services running in the environment, then checks the output to see if each one is up or not. If a service is marked as administratively down, the check will skip it.

##### Mandatory Arguments:
Hostname or IP address of service to test
##### Example Output:

    metric nova-scheduler_on_host_aio1_nova_scheduler_container-e7b92e0f uint32 1
    metric nova-conductor_on_host_aio1_nova_conductor_container-dcddd54a uint32 1
    metric nova-compute_on_host_aio1_nova_compute_container-19824c74 uint32 1
    ...

***
#### cinder_service_check.py

##### Description:
polls the cinder api and gets a list of all cinder services running in the environment, then checks the output to see if each one is up or not. If a service is marked as administratively down, the check will skip it.

##### Mandatory Arguments:
Hostname or IP address of service to test
##### Example Output:

    metric cinder-scheduler_on_host_aio1_cinder_volumes_container-b6ad3de7 uint32 1
    metric cinder-volume_on_host_aio1_cinder_volumes_container-b6ad3de7 uint32 1
    ...

***
#### vg_check.py

##### Description:
Checks the free/used/total space on an lvm volume group and reports as metrics
##### Mandatory Arguments:
Name of volume group to check
##### Example Output:

    status okay
    metric cinder-volumes_vg_total_space int64 107369 Megabytes
    metric cinder-volumes_vg_free_space int64 107369 Megabytes
    metric cinder-volumes_vg_used_space int64 0 Megabytes
    ...

***
#### neutron_service_check.py

##### Description:
polls the neutron api and gets a list of all neutron agents running in the environment, then checks the output to see if each one is up or not. If an agent is marked as administratively down, the check will skip it.

##### Mandatory Arguments:
Hostname or IP address of service to test
##### Example Output:

    metric neutron-metadata-agent_8a1a5b16-8546-4801-a31f-e07dce8c068b_on_host_big3.localdomain uint32 1
    metric neutron-linuxbridge-agent_cac1fd39-e23d-47ea-aa20-99f0accf5584_on_host_aio1_nova_compute_container-19824c74 uint32 1
    metric neutron-dhcp-agent_d89db127-2bc7-473a-bcb0-ac89345397e0_on_host_big3.localdomain uint32 1
    metric neutron-linuxbridge-agent_e86cee43-47bf-42cd-872f-a623e458e549_on_host_big3.localdomain uint32 1
    ...

***
#### neutron_metadata_local_check.py

##### Description:
polls the neutron metadata agent proxies in each network namespace with DHCP enabled to ensure the agent is responsive.

##### Mandatory Arguments:
Hostname or IP address of Neutron API service
##### Example Output:

    metric neutron-metadata-agent-proxy_status uint32 1
    ...

***
#### magnum_service_check.py

##### Description:
Polls the magnum api and gets a list of all magnum services running in the environment, then checks the output to see if each one is up or not. If a service is marked as administratively down, the check will skip it.

##### Mandatory Arguments:
Hostname or IP address of service to test
##### Example Output:

    status okay
    metric magnum-conductor_status uint32 1

***
***
### OTHER CHECKS
***
#### glance_registry_local_check.py

##### Description:
Connects directly to the glance registry and tests status by calling an arbitry url

##### Mandatory Arguments:
IP address of service to test

##### Example Output:

    metric glance_registry_local_status uint32 1
    metric glance_registry_local_response_time uint32 356.917 ms

***
#### memcached_status.py

##### Description:
Connects to a memcached server

##### Mandatory Arguments:
IP address of memcached server

##### Optional Arguments:
--port: port of service to test (default '15672')

##### Example Output:

    metric memcache_api_local_status uint32 1
    metric memcache_total_items uint64 563324 items
    metric memcache_get_hits uint64 4543534 hits
    metric memcache_get_misses uint64 2346565 misses
    metric memcache_curr_connections uint64 42565 connections

***
#### horizon_check.py

##### Description:
Checks the status of the horizon dashboard. First checks that the login page is available, then uses the creds from the openrc-maas file to actually log in.

##### Mandatory Arguments:
IP address of service to test

#### Optional Arguments:

site_name_regexp: name of the horizon dashboard used to find the login page (default: 'openstack dashboard')

##### Example Output:

    metric splash_status_code uint32 200
    metric splash_milliseconds double 83.557 ms
    metric login_status_code uint32 200 http_status
    metric login_milliseconds double 1344.399 ms

***
#### rabbitmq_status.py

##### Description:
connects to an individual member of a rabbit cluster and grabs statistics from the rabbit status API

##### Optional Arguments:
- --host: IP of service to test (default 'localhost')
- --port: port of service to test (default '15672')
- --username: username to test with (default 'guest')
- --password: password to test with (default 'guest')

##### Example Output:

    metric rabbitmq_uptime int64 73439448 ms
    metric rabbitmq_proc_total int64 1048576 processes
    metric rabbitmq_proc_used int64 180 processes
    metric rabbitmq_messages int64 0 messages
    metric rabbitmq_msgs_excl_notifications int64 0 messages
    metric rabbitmq_notification_messages int64 200 messages
    metric rabbitmq_sockets_total int64 3594 fd
    metric rabbitmq_fd_used int64 24 fd
    metric rabbitmq_mem_used int64 41562432 bytes
    metric rabbitmq_fd_total int64 4096 fd
    metric rabbitmq_disk_free_alarm_status uint32 1
    metric rabbitmq_mem_limit int64 3362471936 bytes
    metric rabbitmq_mem_alarm_status uint32 1
    metric rabbitmq_sockets_used int64 1 fd
    metric rabbitmq_messages_unacknowledged int64 0 messages
    metric rabbitmq_messages_ready int64 0 messages

***
#### galera_check.py

##### Description:
connects to an individual member of a galera cluster and checks various statuses to ensure the member is fully synced and considered active

##### Optional Arguments:
- --host: IP of service to test (default 'localhost')
- --port: port of service to test (default '15672')

##### Example Output:

    metric wsrep_replicated_bytes int64 1307 bytes
    metric wsrep_received_bytes int64 299878933 bytes
    metric wsrep_commit_window_size double 1.000143 sequence_delta
    metric wsrep_cluster_size int64 3 nodes
    metric queries_per_second int64 380289 qps
    metric wsrep_cluster_state_uuid string 6a3b85c0-4b07-11e6-8778-3f5baf70ad5c
    metric wsrep_cluster_status string Primary
    metric wsrep_local_state_uuid string 6a3b85c0-4b07-11e6-8778-3f5baf70ad5c
    metric wsrep_local_state_comment string Synced
    metric mysql_max_configured_connections int64 800 connections
    metric mysql_current_connections int64 1 connections
    metric mysql_max_seen_connections int64 2 connections
    metric num_of_open_files int64 14 files
    metric open_files_limit int64 65535 files
    metric innodb_row_lock_time_avg int64 0 milliseconds
    metric innodb_deadlocks int64 0 deadlocks
    metric access_denied_errors int64 0 access_denied_errors
    metric aborted_clients int64 0 aborted_clients
    metric aborted_connects int64 0 aborted_connects

***
#### conntrack_count.py

##### Description:
Returns, as metrics, the values of /proc/sys/net/netfilter/nf_conntrack_count and /proc/sys/net/netfilter/nf_conntrack_max.

The kernel modules nf_conntrack_ipv4 and/or nf_conntrack_ipv6 must be loaded for this plugin to work.

##### Example Output:

    metric nf_conntrack_max uint32 262144
    metric nf_conntrack_count uint32 354

***
#### hp_monitoring.py

##### Description:
Returns metrics indicating the status of parts of HP hardware.

##### Example Output:

    metric hardware_controller_battery_status uint32 1
    metric hardware_controller_cache_status uint32 1
    metric hardware_controller_status uint32 1
    metric hardware_disk_status uint32 1
    metric hardware_memory_status uint32 1
    metric hardware_processors_status uint32 1

***
#### ceph_monitoring.py

##### Description:
Connects to a Ceph cluster with the specified user/key and returns a number of metrics which can be used to monitor general health and availability of that cluster

##### Mandatory Arguments:
- {cluster,mon,osd}: Specify the type of data to return
- --name NAME: Ceph client name to use when connecting to cluster
- --keyring KEYRING: Ceph client keyring to use when connecting to cluster

##### Mandatory Arguments (when osd argument given):
- --osd_ids OSD_IDS: Space-separated list of OSDs, required when `--type osd`

##### Mandatory Arguments (when mon argument given):
- --host HOST: Specific MON to connect to, required when `--type mon`

##### Example Output:
Cluster:

    metric cluster_health uint32 2
    metric monmap_epoch uint32 1
    metric osdmap_epoch uint32 16
    metric osds_total uint32 3
    metric osds_up uint32 3
    metric osds_in uint32 3
    metric osds_kb uint64 495007068
    metric osds_kb_avail uint64 284983032
    metric osds_kb_used uint64 189214596
    metric pgs_active_clean uint32 512
    metric pgs_total uint32 512

MON:

    metric mon_in_quorum uint32 1
    metric mon_health uint32 2

OSDs:

    metric osd.0_up uint32 1
    metric osd.1_up uint32 1
    metric osd.2_up uint32 1
