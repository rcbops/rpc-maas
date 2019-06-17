Validates returned check metrics from the local ``rabbitmq_status.py``
plugin run on the ``rabbitmq_all[0]`` inventory node. This alarm
evaluates a custom queue metric from the RabbitMQ API for active
messages that are in queues that have no consumers.

If the value of ``rabbitmq_msgs_without_consumers`` is greater than the
configured threshold for three successive intervals, a critical alarm
notification is generated. This indicates a large number of messages in
queues that have no consumers. Typically, RabbitMQ performs automatic
cleanup of queues, however, sometimes queues don't meet the criteria and
are left intact (mostly broadcast queues). This will help to identify
large numbers of messages so that they can be removed to free up memory.

The default threshold is identified below and can be overridden with
different values at run time.
