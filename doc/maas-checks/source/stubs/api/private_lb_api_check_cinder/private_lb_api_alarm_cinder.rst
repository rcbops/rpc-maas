Validates returned check metrics from the Cinder API. If the metric
value returned for ``code`` is anything other than ``200`` or ``300``
for three successive intervals, a critical alarm notification is
generated.
