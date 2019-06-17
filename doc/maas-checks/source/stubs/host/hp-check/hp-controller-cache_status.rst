Validates the returned check metric ``hardware_controller_cache_status``
from the local ``hp_monitoring.py`` plugin. The associated check
utilizes the HP CLI utility by executing ``ssacli ctrl all show status``
in order to verify the ``Cache Status`` value is ``OK`` or ``Not
Configured``. If the alarm metric is evaluated as ``0`` for three
successive intervals, a critical alarm notification is generated.
