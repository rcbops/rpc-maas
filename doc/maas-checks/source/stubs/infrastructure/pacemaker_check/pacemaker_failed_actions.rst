Validates the returned check metric ``pacemaker_failed_actions`` from
the local ``pacemaker.py`` plugin. The associated check utilizes the
Pacemaker CLI utility by executing ``pcs status`` in order to verify all
the following values:

* ``Error``
* ``Fail``
* ``Failed``
* ``Faulty``
* ``Notice``
* ``Stopped``
* ``Warning``

If the alarm metric is evaluated as any of the above values for three
successive intervals, a critical alarm notification is generated.
