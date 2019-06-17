Validates the returned check metric ``hardware_memory_status`` from the
local ``openmanage.py`` plugin. The associated check utilizes the Dell
CLI utility by executing ``omreport chassis memory`` in order to verify
all ``Status`` fields are ``Ok``. If the alarm metric is evaluated as
``0`` for three successive intervals, a critical alarm notification is
generated.
