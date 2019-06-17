Validates returned check metrics from the Heat Cloudwatch API. If the
metric value returned for ``code`` is anything other than ``300`` for
three successive intervals, a critical alarm notification is generated.
