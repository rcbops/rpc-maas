Validates returned check metrics from the server via the private network
monitoring poller. If the metric value returned for ``banner_match`` is
an empty string for three successive intervals, a critical alarm
notification is generated.
