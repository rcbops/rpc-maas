Validates returned check metrics from the Designate API. If the metric
value returned for ``code`` is anything other than ``200`` for three
successive intervals, a critical alarm notification is generated.
