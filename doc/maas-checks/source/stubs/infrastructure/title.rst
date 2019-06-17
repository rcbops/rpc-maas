The Infrastructure category is driven by a multitude of custom plugins
that monitor OpenStack supporting services, such as Galera, Memcached
and RabbitMQ. These plugins gather a selection of metrics from the
physical controller nodes and associated containers that OpenStack is
deployed in. These metrics range across the following sub-categories:

- `Container storage <infrastructure.html#container-storage-check>`_ (RPC-O only)
- `Galera <infrastructure.html#galera-check>`_
- `Holland backup <infrastructure.html#holland-local-check>`_ (RPC-O only)
- `Memcached <infrastructure.html#memcached-status>`_
- `NFS <infrastructure.html#nfs-check>`_ (Introspected)
- `Pacemaker <infrastructure.html#pacemaker-check>`_
- `RabbitMQ <infrastructure.html#rabbitmq-status>`_
- `TGTD <infrastructure.html#tgtd-process-check>`_ (Introspected)
- `Multipathd <infrastructure.html#multipathd-process-check>`_ (Introspected)
- `Rsyslogd <infrastructure.html#rsyslogd-process-check>`_ (RPC-O only)
- `Rackspace Monitoring poller <infrastructure.html#maas-poller-fd-count>`_ (PNM only)

The majority of the above checks are contextually deployed based on the
OpenStack inventory. Others are deployed based on introspection, if
services such as private network monitoring pollers or multipathd exist,
the associated functionality will be deployed.
