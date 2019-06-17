At deployment time, the playbooks enumerate each host to determine
mounted filesystems. All detected mounted filesystems will have a
monitoring check deployed. The filesystem check utilizes the native
``agent.filesystem`` functionality within the
``rackspace-monitoring-agent`` to build metrics for filesystem-related
usage.

Metrics derived from the ``agent.filesystem`` check type can be found in the
Rackspace Monitoring `agent.filesystem
<https://developer.rackspace.com/docs/rackspace-monitoring/v1/tech-ref-info/check-type-reference/#agent-filesystem>`_
reference documentation.
