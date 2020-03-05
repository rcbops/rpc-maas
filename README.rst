Monitoring as a Service (MaaS) for Rackspace Private Cloud
##########################################################
:tags: openstack, rpc, cloud, ansible, maas, rackspace
:category: \*nix

Deployment, setup and installation of Rackspace MaaS for Rackspace Private clouds.

RPC-MaaS Monitoring
-------------------

These playbooks allow deployers to monitor clouds using Rackspace Monitoring as a Service.
The playbooks can be used with OpenStack-Ansible or on their own using Ansible static
inventory.


Documentation
-------------

Documentation for the project can be found under: docs/source/index.rst

To build the documentation simply execute ``tox -e docs``.


Submitting Bugs
---------------

Please submit all bugs to the rpc-maas repository:
https://jira.rax.io/browse/RPCOS


Local Testing
-------------

To test these playbooks within a local environment you will need a single server with
at leasts 8GiB of RAM and 40GiB of storage on root. Running an m1.medium (openstack)
flavor size is generally enough to get an environment online.

To run the local functional tests execute the `run-tests.sh` script out of the tests
directory. This will create an OpenStack AIO and run the RPC-MaaS playbooks against
the newly constructed environment.

.. code-block:: bash

    tests/run-tests.sh
