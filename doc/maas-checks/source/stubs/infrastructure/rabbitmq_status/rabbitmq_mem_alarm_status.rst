Validates returned check metrics from the local ``rabbitmq_status.py``
plugin run on the ``rabbitmq_all[0]`` inventory node. This alarm
evaluates the output of value ``mem_alarm`` from the RabbitMQ API.

If the boolean metric ``rabbitmq_mem_alarm_status`` is ``0`` for three
successive intervals, a critical alarm notification is generated. This
indicates that a memory alarm is in effect due to RabbitMQ consuming 40%
of installed RAM.

.. note::

    This does not prevent the RabbitMQ from using more than 40%, it is
    merely the point at which publishers are throttled.
