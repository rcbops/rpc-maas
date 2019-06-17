The memory_check utilizes native ``agent.memory`` functionality within
the ``rackspace-monitoring-agent`` to build metrics for memory related
usage on a given host. For all hosts outside the ``infra_hosts``
inventory group, metrics are generated but not evaluated in any form.
Therefore, no alarm notifications or corresponding tickets are created.
For infrastructure hosts that fall in scope, metrics are generated for
current ``actual_used`` and ``total`` memory values.

Metrics derived from the ``agent.memory`` check type can be found in the
Rackspace Monitoring `agent.memory
<https://developer.rackspace.com/docs/rackspace-monitoring/v1/tech-ref-info/check-type-reference/#agent-memory>`_
reference documentation.
