from rally import consts
from rally.plugins.openstack import scenario
from rally.plugins.openstack.scenarios.neutron import utils
from rally.task import validation

@validation.required_services(consts.Service.NEUTRON)
@validation.required_openstack(users=True)
@scenario.configure(context={"cleanup": ["neutron"]},
                    name=("NeutronSecurityGroup"
                          ".create_update_and_delete_security_groups"))
class CreateUpdateAndDeleteSecurityGroups(utils.NeutronScenario):

    def run(self, security_group_create_args=None,
            security_group_update_args=None):
        """Create and update Neutron security-groups.

        Measure the "neutron security-group-create" and "neutron
        security-group-update" command performance.

        :param security_group_create_args: dict, POST /v2.0/security-groups
                                           request options
        :param security_group_update_args: dict, PUT /v2.0/security-groups
                                           update options
        """
        security_group_create_args = security_group_create_args or {}
        security_group_update_args = security_group_update_args or {}
        security_group = self._create_security_group(
            **security_group_create_args)
        self._update_security_group(security_group,
                                    **security_group_update_args)
        self._delete_security_group(security_group)
