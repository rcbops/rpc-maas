The *disk_utilisation_<key>* check utilizes a custom plugin,
``disk_utilisation.py``, which runs locally on all hosts to generate
metrics for specific disk I/O values. This targets ``infra_hosts`` and
evaluates I/O on parent disk devices originating from ``/`` and
``/openstack`` filesystems. Notifications are generated when evaluation
for the ``disk_utilisation_<key>`` metric is higher than a given
threshold. In these situations, it typically indicates a problem which
may be impacting to the environment.

.. note::

    For all hosts outside the ``infra_hosts`` inventory group, metrics
    are generated but not evaluated. Therefore, no alarm notifications
    or corresponding tickets are created for high I/O. This includes node
    types such as Cinder, Nova, Swift, and Ceph.
