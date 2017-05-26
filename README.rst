Monitoring as a Service (MaaS) for Rackspace Private Cloud
##########################################################
:tags: openstack, rpc, cloud, ansible, maas, rackspace
:category: \*nix

Deployment, setup and installation of Rackspace MaaS for Rackspace Private clouds.

RPC-MaaS Monitoring
###################

These playbooks allow deployers to monitor clouds using Rackspace Monitoring as a Service.
The playbooks can be used with OpenStack-Ansible or on their own using Ansible static
inventory.

Example usage with Ansible static Inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    ansible-playbook -i tests/inventory playbooks/site.yml


Example usage with OpenStack-Ansible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    export ANSIBLE_INVENTORY="/opt/openstack-ansible/playbooks/inventory"
    openstack-ansible playbooks/site.yml


Validating the deployment
~~~~~~~~~~~~~~~~~~~~~~~~~

After deployment you can run a local validation playbook to ensure that everything
is working as expected which can be done with static inventory as well as within an
OpenStack-Ansible deployment.


**With OpenStack-Ansible**

.. code-block:: bash

    # Set the inventory path so Ansible knows how to do an inventory run.
    export ANSIBLE_INVENTORY="/opt/openstack-ansible/playbooks/inventory"

    # Run the test playbook
    openstack-ansible playbooks/maas-verify.yml


**With Static Inventory**

.. code-block:: bash

    # Run the test playbook
    ansible-playbook -i inventory playbooks/maas-verify.yml


Documentation
#############

Documentation for the project can be found under: docs/source/index.rst

To build the documentation simply execute ``tox -e docs``.


Submitting Bugs
###############

Please submit all bugs to the rpc-maas repository:
https://github.com/rcbops/rpc-maas/issues
