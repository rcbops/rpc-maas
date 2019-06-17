Validates returned check metrics from the local
``service_api_local_check.py`` plugin run across ``heat_api_cloudwatch``
nodes. If the ``heat_cw_api_local_status`` metric is ``0`` for three
successive intervals, a critical alarm notification is generated. This
indicates the Heat Cloudwatch API is down on the associated backend
container.
