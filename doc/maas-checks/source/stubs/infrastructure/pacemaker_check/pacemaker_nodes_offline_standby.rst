Validates the returned check metric ``pacemaker_resource_stop`` from the
local ``pacemaker.py`` plugin. The associated check utilizes the
Pacemaker CLI utility by executing ``pcs status nodes`` in order to
verify all the following values associated to the following keys:

* ``Standby``
* ``Offline``

If the alarm metric is evaluated with a value to the above keys for
three successive intervals, a critical alarm notification is generated.
