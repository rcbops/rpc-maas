Validates returned check metrics from the local ``rabbitmq_status.py``
plugin run on the ``rabbitmq_all[0]`` inventory node. This alarm
evaluates a custom connection metric for all active connections from the
RabbitMQ API.

If the value of ``rabbitmq_max_channels_per_conn`` is greater than the
configured threshold for three successive intervals, a critical alarm
notification is generated. This indicates a large number of channels per
connection in RabbitMQ, which typically results in increased CPU
consumption on the cluster node.

The default threshold is identified below and can be overridden with
different values at run time.
