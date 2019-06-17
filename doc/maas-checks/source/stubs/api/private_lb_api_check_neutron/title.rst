Queries the OpenStack Neutron API using local private pollers and
standard HTTP GET method. The check returns metrics that are used to
validate and gauge API uptime around Neutron. This check is deployed to
each controller node, but only enabled on the first node of the
inventory group.
