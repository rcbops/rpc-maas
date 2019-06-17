Utilizes a custom plugin, ``service_api_local_check.py``, which runs
locally to generate metrics from each ``heat_api_cfn`` (infrastructure)
node. This check subverts the typical load balanced Heat CloudFormation
API in order to validate functionality at the container level. This
provides an additional level of granularity to ensure the Heat
CloudFormation API is operationally healthy across all backends.

Alarms associated with this monitoring check utilize the
``heat_cfn_api_local_status`` metric, which is a boolean:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``heat_cfn_api_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/service_api_local_check.py \
      heat_cfn 172.29.237.226 8000
    status okay
    metric client_success uint32 1
    metric heat_cfn_api_local_status uint32 1
    metric heat_cfn_api_local_response_time double 4.694 ms
