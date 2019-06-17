Queries the OpenStack Heat Cloudwatch API using remote pollers and
standard HTTP GET method. The check returns metrics that are used to
validate and gauge API uptime around Heat Cloudwatch. This check is
deployed to each controller node, but only enabled on the first node of
the inventory group.
