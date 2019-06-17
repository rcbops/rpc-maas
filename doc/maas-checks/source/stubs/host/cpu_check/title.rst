The *cpu_check* utilizes native ``agent.cpu`` functionality within the
``rackspace-monitoring-agent`` to build metrics for CPU-related usage on
a given host. For all hosts outside the ``infra_hosts`` inventory group,
metrics are generated but not evaluated in any form. Therefore, no alarm
notifications or corresponding tickets are created. For infrastructure
hosts that fall in scope, idle CPU time is measured and evaluated when
the ``idle_percent_average`` metric falls below a given threshold. In
these situations, it typically indicates a problem which may be
impacting to the environment.

Metrics derived from the ``agent.cpu`` check type can be found in the
Rackspace Monitoring `agent.cpu
<https://developer.rackspace.com/docs/rackspace-monitoring/v1/tech-ref-info/check-type-reference/#agent-cpu>`_
reference documentation.
