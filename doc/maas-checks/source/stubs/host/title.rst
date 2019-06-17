The Host category is driven by a multitude of agent-based functionality
that is natively part of the ``rackspace-monitoring-agent``, along with
some additional custom local plugins. These plugins gather a gamut of
metrics from the physical nodes that OpenStack is deployed on. These
metrics range across the following sub-categories:

- `CPU usage <host.html#cpu-check>`_ (*CDM*)
- `Memory usage <host.html#memory-check>`_ (*CDM*)
- `Disk I/O utilization <host.html#disk-utilisation-key>`_ (*CDM*)
- `Network interface TX/RX errors <host.html#network-stats-check>`_
- `Bonding interface status <host.html#host-bonding-iface-status-check>`_
- `Conntrack limits <host.html#conntrack-count>`_
- `Filesystem usage <host.html#filesystem-filesystem>`_ (all mounted filesystems)
- `Ping validation <host.html#private-ping-check>`_ (primary IPv4 address)
- `SSH validation <host.html#private-ssh-check>`_ (primary IPv4 address)
- Hardware

  * `HP processor status <host.html#hp-check>`_
  * `HP memory status <host.html#hp-check>`_
  * `HP power supply status <host.html#hp-check>`_
  * `HP disk status <host.html#hp-check>`_
  * `HP RAID controller status <host.html#hp-check>`_
  * `HP RAID battery status <host.html#hp-check>`_
  * `HP RAID cache status <host.html#hp-check>`_
  * `Dell processor status <host.html#openmanage-processors>`_
  * `Dell memory status <host.html#openmanage-memory>`_
  * `Dell power supply status <host.html#openmanage-pwrsupplies>`_
  * `Dell virtual/physical disk status <host.html#openmanage-vdisk>`_

.. note::

    The variable ``maas_raxdc`` determines whether hardware-specific
    checks and alarms are deployed for an environment. This
    functionality is exclusive for Rackspace data center and OpenStack
    Everywhere deployments and must be enabled by a Rackspace Engineer
    prior to deployment.

At a minimum, metrics and alarms are deployed across all hosts. However,
items labeled as *CDM* in the above list do not generate alarm
notifications, which would result in a ticket, for any physical node
outside of the ``infra_hosts`` inventory group. This is enforced as
Rackspace engineers are typically unable to remediate issues as a result
of overallocation or general high utilization of underlying resources.
