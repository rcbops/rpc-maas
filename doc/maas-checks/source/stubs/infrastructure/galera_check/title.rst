The *galera* check utilizes a custom plugin, `galera_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/galera_check.py>`_,
which runs locally on controller nodes to generate a set of metrics
regarding various aspects of overall galera cluster health. While this
check is deployed to all controller nodes, it is only enabled on the
physical node of ``galera_all[0]`` from the inventory.

The following subset of galera metrics are used by ticket generating
alarms:

* `Cluster size <infrastructure.html#alarm-wsrep-cluster-size>`_ (``wsrep_cluster_size``)
* `Cluster state <infrastructure.html#alarm-wsrep-local-state>`_ (``wsrep_local_state_comment``)
* `Connections limits <infrastructure.html#alarm-percentage-used-mysql-connections>`_ (``mysql_current_connections``, ``mysql_max_configured_connections``)
* `File descriptor limits (mysql) <infrastructure.html#alarm-open-file-size-limit-reached>`_ (``num_of_open_files``, ``open_files_limit``)
* `InnoDB row lock duration <infrastructure.html#alarm-innodb-row-lock-time-avg>`_ (``innodb_row_lock_time_avg``)
* `InnoDB deadlock rate <infrastructure.html#alarm-innodb-deadlocks>`_ (``innodb_deadlocks``)
* `Denied connections <infrastructure.html#alarm-access-denied-errors>`_ (``access_denied_errors``)
* `Aborted connections <infrastructure.html#alarm-aborted-connects>`_ (``aborted_connects``)

The following snippet is an example of properly executing the
``galera_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/galera_check.py \
      -H 10.0.238.123
    status okay
    metric wsrep_replicated_bytes int64 2930806296 bytes
    metric wsrep_received_bytes int64 279206 bytes
    metric wsrep_commit_window_size double 1.009457 sequence_delta
    metric wsrep_cluster_size int64 3 nodes
    metric queries_per_second int64 39840092 qps
    metric wsrep_cluster_state_uuid string 1074b575-a3f9-11e9-871b-6edd15163d6d
    metric wsrep_cluster_status string Primary
    metric wsrep_local_state_uuid string 1074b575-a3f9-11e9-871b-6edd15163d6d
    metric wsrep_local_state_comment string Synced
    metric mysql_max_configured_connections int64 400 connections
    metric mysql_current_connections int64 380 connections
    metric mysql_max_seen_connections int64 387 connections
    metric num_of_open_files int64 26 files
    metric open_files_limit int64 65535 files
    metric innodb_row_lock_time_avg int64 40 milliseconds
    metric innodb_deadlocks int64 0 deadlocks
    metric access_denied_errors int64 480 access_denied_errors
    metric aborted_clients int64 6212 aborted_clients
    metric aborted_connects int64 480 aborted_connects
