Queries the OpenStack Swift API using remote pollers and standard HTTP
GET method. The check returns metrics that are used to validate a test
container is up and available within Swift. This check is deployed to
each swift proxy node, but only enabled on the first node of the
inventory group.
