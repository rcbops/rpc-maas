Validates the returned check metric ``hardware_disk_status`` from the
local ``hp_monitoring.py`` plugin. The associated check utilizes the HP
CLI utility by executing ``ssacli ctrl all show config`` in order to
verify all ``logicaldrive`` values return ``OK`` or ``OK, Encrypted``.
If the alarm metric is evaluated as ``0`` for three successive
intervals, a critical alarm notification is generated.
