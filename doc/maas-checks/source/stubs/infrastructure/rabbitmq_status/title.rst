The *rabbitmq_status* check utilizes a custom plugin, `rabbitmq_status.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/templates/rax-maas/plugins/rabbitmq_status.py>`_,
which runs locally on controller nodes to generate a set of metrics
regarding various aspects of overall RabbitMQ cluster health. While this
check is deployed to all controller nodes, it is only enabled on the
physical node of ``rabbitmq_all[0]`` from the inventory.

The following subset of RabbitMQ metrics are used by ticket generating
alarms:

* `Disk alarm <infrastructure.html#alarm-rabbitmq-disk-free-alarm-status>`_ (``rabbitmq_disk_free_alarm_status``)
* `Memory alarm <infrastructure.html#alarm-rabbitmq-mem-alarm-status>`_ (``rabbitmq_mem_alarm_status``)
* `Channels per connection <infrastructure.html#alarm-rabbitmq-max-channels-per-conn>`_ (``rabbitmq_max_channels_per_conn``)
* `File descriptor limits (rabbitmq) <infrastructure.html#alarm-rabbitmq-fd-used-alarm-status>`_ (``rabbitmq_fd_used`` and ``rabbitmq_fd_total``)
* `Process limits <infrastructure.html#alarm-rabbitmq-proc-used-alarm-status>`_ (``rabbitmq_proc_used`` and ``rabbitmq_proc_total``)
* `Socket limits <infrastructure.html#alarm-rabbitmq-socket-used-alarm-status>`_ (``rabbitmq_sockets_used`` and ``rabbitmq_sockets_total``)
* `Queue growth rate <infrastructure.html#alarm-rabbitmq-qgrowth-excl-notifications>`_ (``rabbitmq_msgs_excl_notifications``)
* `Messages excluding notifications <infrastructure.html#alarm-rabbitmq-msgs-excl-notifications>`_ (``rabbitmq_msgs_excl_notifications``)
* `Messages without consumers <infrastructure.html#alarm-rabbitmq-msgs-without-consumers>`_ (``rabbitmq_msgs_without_consumers``)

The following snippet is an example of properly executing the
``rabbitmq_status`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/rabbitmq_status.py \
      -H 10.0.239.2 \
      -n infra1-rabbit-mq-container-da6c7265 \
      -U maas_user \
      -p <password> \
      --http
    status okay
    metric rabbitmq_msgs_excl_notifications int64 0 messages
    metric rabbitmq_sockets_total int64 58890 fd
    metric rabbitmq_mem_used int64 143138816 bytes
    metric rabbitmq_fd_total int64 65536 fd
    metric rabbitmq_notification_messages int64 0 messages
    metric rabbitmq_uptime int64 1197907362 ms
    metric rabbitmq_deliver_get int64 1971906 messages
    metric rabbitmq_max_channels_per_conn int64 0 channels
    metric rabbitmq_fd_used int64 115 fd
    metric rabbitmq_publish int64 1795852 messages
    metric rabbitmq_messages_unacknowledged int64 0 messages
    metric rabbitmq_mem_alarm_status uint32 1
    metric rabbitmq_msgs_without_consumers int64 18 messages
    metric rabbitmq_get int64 0 messages
    metric rabbitmq_deliver int64 1971906 messages
    metric rabbitmq_sockets_used int64 71 fd
    metric rabbitmq_proc_total int64 1048576 processes
    metric rabbitmq_queues_without_consumers int64 3 queues
    metric rabbitmq_ack int64 1971903 messages
    metric rabbitmq_proc_used int64 2074 processes
    metric rabbitmq_messages int64 18 messages
    metric rabbitmq_disk_free_alarm_status uint32 1
    metric rabbitmq_mem_limit int64 3363917824 bytes
    metric rabbitmq_messages_ready int64 18 messages
