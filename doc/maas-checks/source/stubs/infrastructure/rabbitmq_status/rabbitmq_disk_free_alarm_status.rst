Validates returned check metrics from the local ``rabbitmq_status.py``
plugin run on the ``rabbitmq_all[0]`` inventory node. This alarm
evaluates the output of value ``disk_free_alarm`` from the RabbitMQ API.

If the boolean metric ``rabbitmq_disk_free_alarm_status`` is ``0`` for
three successive intervals, a critical alarm notification is generated.
This indicates that a disk alarm is in effect due to RabbitMQ dropping
below the configured limit.
