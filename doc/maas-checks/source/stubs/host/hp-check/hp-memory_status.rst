Validates the returned check metric ``hardware_memory_status`` from the
local ``hp_monitoring.py`` plugin. The associated check utilizes the HP
CLI utility by executing ``hpasmcli -s 'show dimm'`` in order to verify
the ``Status`` value is ``OK``. If the alarm metric is evaluated as
``0`` for three successive intervals, a critical alarm notification is
generated.
