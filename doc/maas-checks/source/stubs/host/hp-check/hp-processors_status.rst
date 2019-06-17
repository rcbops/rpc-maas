Validates the returned check metric ``hardware_processors_status`` from
the local ``hp_monitoring.py`` plugin. The associated check utilizes the
HP CLI utility by executing ``hpasmcli -s 'show server'`` in order
to verify the ``Status`` value is ``OK``. If the alarm metric is
evaluated as ``0`` for three successive intervals, a critical alarm
notification is generated.
