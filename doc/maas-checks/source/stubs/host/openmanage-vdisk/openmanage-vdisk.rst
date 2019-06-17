Validates the returned check metric ``hardware_vdisk_status`` from the
local ``openmanage.py`` plugin. The associated check utilizes the Dell
CLI utility by executing ``omreport storage vdisk`` in order to verify
all ``Status`` field(s) are ``Ok``. If the alarm metric is evaluated as
``0`` for three successive intervals, a critical alarm notification is
generated.
