Queries the OpenStack Swift API using local private pollers and standard
HTTP GET method. The check returns metrics that are used to validate and
gauge API uptime around Swift. This check is deployed to each swift
proxy node, but only enabled on the first node of the inventory group.
