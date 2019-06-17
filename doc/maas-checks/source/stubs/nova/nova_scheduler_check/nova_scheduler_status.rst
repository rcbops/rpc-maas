Validates returned check metrics from the local
``nova_service_check.py`` plugin run across ``nova_scheduler`` nodes. If
the ``nova-scheduler_status`` metric is ``No`` for three successive
intervals, a critical alarm notification is generated. This indicates
the ``nova-scheduler`` service is down on the associated host.

In the event the OpenStack SDK is unable to establish a connection to
the Nova API, it will generate a metric stating such. In turn, this
will evaluate as a non-ticket generating event, which will prevent a
fallout of notifications that result in tickets being generated.
