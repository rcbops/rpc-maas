Validates returned check metrics from the local ``rabbitmq_status.py``
plugin run on the ``rabbitmq_all[0]`` inventory node. This alarm
evaluates the output of values ``fd_used`` and ``fd_total`` from the
RabbitMQ API.

If the percentage of ``rabbitmq_fd_used`` and ``rabbitmq_fd_total``
metrics reach the threshold for three successive intervals, a critical
alarm notification is generated. This indicates that the open file limit
is being reached.

The default threshold is identified below and can be overridden with
different values at run time.
