Validates the returned check metric ``hardware_controller_status`` from
the local ``hp_monitoring.py`` plugin. The associated check utilizes the
HP CLI utility by executing ``ssacli ctrl all show status`` in order to
verify the ``Controller Status`` value is ``OK``. If the alarm metric is
evaluated as ``0`` for three successive intervals, a critical alarm
notification is generated.
