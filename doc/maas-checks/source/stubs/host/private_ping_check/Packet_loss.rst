Validates returned check metrics from the server via the private network
monitoring poller. If the metric value returned for ``available`` is
less than 80% (2 of 6 ICMP requests/replies) for three successive
intervals, a critical alarm notification is generated.
