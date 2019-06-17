Validates returned check metrics from the local ``iptables_check.py``
plugin run across ``nova_compute`` nodes. If the ``iptables_status``
metric is ``0`` for three successive intervals, a critical alarm
notification is generated. This indicates that security groups are not
currently enforcing on the associated nova compute node.
