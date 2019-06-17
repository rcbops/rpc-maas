Validates returned check metrics from the local ``horizon_check.py``
plugin runs on the ``horizon[0]`` node. If the ``horizon_local_status``
metric is ``0`` for three successive intervals, a critical alarm
notification is generated. This indicates the Horizon dashboard is down
on the VIP.
