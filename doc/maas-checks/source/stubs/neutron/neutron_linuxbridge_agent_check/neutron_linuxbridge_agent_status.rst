Validates returned check metrics from the local
``neutron_service_check.py`` plugin run across
``neutron_linuxbridge_agent`` nodes. If the
``neutron-linuxbridge-agent_status`` metric is ``No`` for three
successive intervals, a critical alarm notification is generated. This
indicates the Neutron Linux bridge agent is down on the associated
backend container or host.

In the event the OpenStack SDK is unable to establish a connection to
the Neutron API, it will generate a metric matching regex ``.*cannot
reach API.*``. In turn, this will evaluate as a non-ticket generating
event, which will prevent a fallout of notifications that result in
tickets being generated.
