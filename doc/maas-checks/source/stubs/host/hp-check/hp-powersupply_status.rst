Validates the returned check metric ``hardware_powersupply_status`` from
the local ``hp_monitoring.py`` plugin. The associated check utilizes the
HP CLI utility by executing ``hpasmcli -s 'show powersupply'`` in order
to verify the ``Condition`` value is ``OK``. If the alarm metric is
evaluated as ``0`` for three successive intervals, a critical alarm
notification is generated.
