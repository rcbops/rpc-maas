Validates returned check metrics from the local ``rabbitmq_status.py``
plugin run on the ``rabbitmq_all[0]`` inventory node. This alarm
evaluates a custom queue metric from the RabbitMQ API for active
messages that are in queues that have consumers.

If the value of ``rabbitmq_msgs_excl_notifications`` is greater than the
configured threshold for three successive intervals, a critical alarm
notification is generated. This indicates a large number of messages in
queues that are not notifications. This typically means that the cluster
is overloaded or has a problem processing messages in a timely manner.

The default threshold is identified below and can be overridden with
different values at run time.
