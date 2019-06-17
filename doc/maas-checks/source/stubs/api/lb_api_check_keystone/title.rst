Queries the OpenStack Keystone API using remote pollers and standard
HTTP GET method. The check returns metrics that are used to validate and
gauge API uptime around Keystone. This check is deployed to each
controller node, but only enabled on the first node of the inventory
group.
