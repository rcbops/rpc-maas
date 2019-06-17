Utilizes a custom plugin, ``glance_api_local_check.py``, which runs
locally to generate metrics from each ``glance_api`` (infrastructure)
node. This check subverts the typical load balanced Glance API in order
to validate functionality at the container level. This provides an
additional level of granularity to ensure the Glance API is
operationally healthy across all backends.

Alarms associated with this monitoring check utilize the
``glance_api_local_status`` metric, which is a boolean:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``glance_api_local_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/glance_api_local_check.py \
      --protocol http \
      --port 9292 \
      10.0.239.132
    status okay
    metric client_success uint32 1
    metric glance_api_local_status uint32 1
    metric glance_api_local_response_time double 645.100 ms
    metric glance_active_images uint32 0 images
    metric glance_queued_images uint32 0 images
    metric glance_killed_images uint32 0 images
