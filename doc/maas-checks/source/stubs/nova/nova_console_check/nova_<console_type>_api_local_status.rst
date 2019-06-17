Validates returned check metrics from the local
``service_api_local_check.py`` plugin run across ``nova_console`` nodes.
If the ``nova_<console_type>_api_local_status`` metric is ``0`` for
three successive intervals, a critical alarm notification is generated.
This indicates the associated nova ``<console_type>`` service is down on
the associated backend.
