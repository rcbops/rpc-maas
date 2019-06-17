Utilizes a custom ``agent.plugin`` check type, ``ceph_monitoring.py``.
The plugin runs locally from each Ceph OSD node in the inventory. The
OSD's are determined from the OSD tree during playbook execution. Each
OSD will have a separate check template created with a single alarm
indicating whether the OSD is up. If 60 unique OSD ID's exist, 60
separate checks will be created during the monitoring deployment. As
this information is queried once per minute, per OSD, the OSD status is
queried locally using ``ceph daemon osd.<ID> status`` so there is no
impact to the Ceph mons API.

The ``osd.<ID>_up`` metric is a boolean:

.. code-block:: console

    0: OSD is down
    1: OSD is up

An example of properly executing the ``ceph_osd_<ID>_stats`` plugin:

.. code-block:: console

  root@osd1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
    /usr/lib/rackspace-monitoring-agent/plugins/ceph_monitoring.py \
    --name client.raxmon \
    --keyring /etc/ceph/ceph.client.raxmon.keyring \
    osd --osd_id 23
  status okay
  metric osd.23_up uint32 1
