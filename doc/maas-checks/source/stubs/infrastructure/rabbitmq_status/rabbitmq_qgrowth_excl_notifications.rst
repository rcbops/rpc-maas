Validates returned check metrics from the local ``rabbitmq_status.py``
plugin run on the ``rabbitmq_all[0]`` inventory node. This alarm uses a
`rate-over-time
<https://developer.rackspace.com/docs/rackspace-monitoring/v1/tech-ref-info/alert-triggers-and-alarms/#constructs-with-function-modifiers>`_
function to evaluate a custom queue metric from the RabbitMQ API for active
messages that are in queues with consumers.

If the value of ``rabbitmq_msgs_excl_notifications`` has a rate value
greater than the configured threshold for three successive intervals, a
critical alarm notification is generated. This indicates a large spike
in the number of messages in queues that are being actively consumed.

The default threshold is identified below and can be overridden with
different values at run time. This can sometimes be due to batch
workloads and should be adjusted accordingly.
