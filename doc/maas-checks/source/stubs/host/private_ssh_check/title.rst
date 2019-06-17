With private network monitoring configured within a Rackspace data
center (RDC) or Customer data center (CDC), the *private_ssh* check is
deployed using local private pollers with the standard TCP network
protocol. This is deployed to all physical hosts within an environment's
inventory. The check is scoped to the IP address associated with the
Ansible fact ``ansible_default_ipv4.address`` of each host and returns
metrics that are used to validate and gauge server responsiveness to SSH
connections. These metrics are identical to the standard Rackspace
Monitoring ``remote.tcp`` check type. The reference documentation for
`remote.tcp
<https://developer.rackspace.com/docs/rackspace-monitoring/v1/tech-ref-info/check-type-reference/#remote-tcp>`_
outlines these attributes in more detail.

In some situations, such as when a storage controller locks up, SSH
connection attempts to a server may still result in a banner being
returned, even though the server is inaccessible. For these instances,
the `Agent Health
<https://support.rackspace.com/how-to/introduction-to-agent-health-monitoring>`_
check is relied upon to properly gauge whether a server is up or down.
All agent health checks and alarms are automatically provisioned when an
agent initially connects to the Rackspace Monitoring infrastructure and
associates itself to an entity.

.. note::

    In RDC without private network monitoring, SSH checks are
    automatically deployed when a server is marked ``Online/Complete``
    within internal Rackspace systems. This check uses the public
    Rackspace Monitoring poller zones and targets the public NAT of each
    server, if one exists.
