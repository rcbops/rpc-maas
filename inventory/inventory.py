#!/usr/bin/env python3
import sys
import json
import yaml


def read_yaml_file(file_path):
    with open(file_path, 'r') as yaml_file:
        data = yaml.safe_load(yaml_file)
    return data


user_maas_variables = read_yaml_file("user_maas_variables.yml")


overcloud_variables = read_yaml_file(
    f"/home/stack/overcloud-deploy/{user_maas_variables['overcloud_stack']}/{user_maas_variables['overcloud_stack']}-export.yaml")

overcloud_environment_variable = read_yaml_file(
    f"/home/stack/overcloud-deploy/{user_maas_variables['overcloud_stack']}/environment/tripleo-{user_maas_variables['overcloud_stack']}-environment.yaml")

undercloud_tripleo_ansible_inventory = read_yaml_file(
    "/home/stack/tripleo-deploy/undercloud/tripleo-ansible-inventory.yaml")

inventory_data = {
    "glance_api": {

        "children": [
            "Controller"
        ]
    },
    "rabbitmq_all": {
        "children": [
            "Controller"
        ]
    },
    "neutron_dhcp_agent": {
        "children": [
            "neutron_dhcp"
        ]
    },
    "neutron_server": {
        "children": [
            "neutron_api"
        ]
    },
    "nova_api_os_compute": {
        "children": [
            "nova_api"
        ]
    },
    "rsyslog_all": {
        "children": [
            "Controller"
        ]
    },
    "osds": {
        "children": [
            "ceph_osd"
        ]
    },
    "swift_storage": {

        "children": [
            "Controller"
        ]
    },
    "utility_all": {
        "children": [
            "Undercloud"
        ]
    },
    "nova_api_metadata": {
        "children": [
            "nova_metadata"
        ]
    },
    "neutron_metadata_agent": {
        "children": [
            "neutron_metadata"
        ]
    },
    "glance_all": {
        "children": [
            "glance_api",
            "glance_registry_disabled"
        ]
    },
    "heat_api_cloudwatch_disabled": {

        "children": [
            "Controller"
        ]
    },
    "rgws": {
        "children": [
            "ceph_rgw"
        ]
    },
    "nova_all": {
        "children": [
            "nova_placement",
            "nova_conductor",
            "nova_metadata",
            "nova_consoleauth",
            "nova_api",
            "nova_migration_target",
            "nova_compute",
            "nova_scheduler",
            "nova_libvirt",
            "nova_vnc_proxy"
        ]
    },
    "nova_console": {
        "children": [
            "nova_consoleauth"
        ]
    },
    "heat_api": {

        "children": [
            "Controller"
        ]
    },
    "shared-infra_hosts": {
        "children": [
            "Controller"
        ]
    },
    "nova_scheduler": {

        "children": [
            "Controller"
        ]
    },
    "keystone_all": {
        "children": [
            "Controller"
        ]
    },
    "neutron_metadata": {

        "children": [
            "Controller"
        ]
    },
    "all": {
        "children": [
            "hosts"
        ]
    },
    "nova_placement": {

        "children": [
            "Controller"
        ]
    },
    "galera": {
        "children": [
            "Controller"
        ]
    },
    "memcached_all": {
        "children": [
            "Controller"
        ]
    },
    "heat_all": {
        "children": [
            "heat_api",
            "heat_api_cloudwatch_disabled",
            "heat_engine",
            "heat_api_cfn"
        ]
    },
    "ceph_osd": {

        "children": [
            "CephStorage",
            "CephStorage_Perf"
        ]
    },
    "swift_ringbuilder": {

        "children": [
            "Controller"
        ]
    },
    "nova_api": {

        "children": [
            "Controller"
        ]
    },
    "swift_all": {
        "children": [
            "swift_ringbuilder",
            "swift_storage",
            "swift_proxy"
        ]
    },
    "neutron_dhcp": {

        "children": [
            "Controller"
        ]
    },
    "nova_libvirt": {

        "children": [
            "Compute"
        ]
    },
    "neutron_all": {
        "children": [
            "neutron_metadata",
            "neutron_dhcp",
            "neutron_plugin_ml2",
            "neutron_ovs_agent",
            "neutron_api",
            "neutron_l3"
        ]
    },
    "nova_vnc_proxy": {

        "children": [
            "Controller"
        ]
    },
    "neutron_plugin_ml2": {

        "children": [
            "Compute",
            "Controller"
        ]
    },
    "horizon": {

        "children": [
            "Controller"
        ]
    },
    "horizon_all": {
        "children": [
            "Controller"
        ]
    },
    "nova_metadata": {

        "children": [
            "Controller"
        ]
    },
    "heat_engine": {

        "children": [
            "Controller"
        ]
    },
    "cinder_api": {

        "children": [
            "Controller"
        ]
    },
    "neutron_l3_agent": {
        "children": [
            "neutron_l3"
        ]
    },
    "cinder_all": {
        "children": [
            "cinder_api",
            "cinder_volume",
            "cinder_scheduler"
        ]
    },
    "nova_migration_target": {

        "children": [
            "Compute"
        ]
    },
    "neutron_openvswitch_agent": {
        "children": [
            "neutron_ovs_agent"
        ]
    },
    "glance_registry_disabled": {

        "children": [
            "Controller"
        ]
    },
    "nova_conductor": {

        "children": [
            "Controller"
        ]
    },
    "nova_compute": {
        "children": [
            "Compute"
        ]
    },
    "galera_all": {
        "children": [
            "Controller"
        ],
        "vars": {
            "galera_root_password": overcloud_variables['parameter_defaults']['MysqlRootPassword']
        }
    },
    "neutron_ovs_agent": {

        "children": [
            "Compute",
            "Controller"
        ]
    },
    "swift_proxy": {

        "children": [
            "Controller"
        ]
    },
    "cinder_scheduler": {

        "children": [
            "Controller"
        ]
    },
    "neutron_l3": {

        "children": [
            "Controller"
        ]
    },
    "nova_consoleauth": {

        "children": [
            "Controller"
        ]
    },
    "cinder_volume": {

        "children": [
            "Controller"
        ]
    },
    "hosts": {
        "children": [
            "overcloud",
            "Undercloud"
        ]
    },
    "overcloud": {
        "children": [
            "CephStorage",
            "CephStorage_Perf",
            "Compute",
            "Controller"
        ],
        "vars": {
            "provisioning_interface": user_maas_variables['overcloud_provisioning_interface'],
            "internal_lb_vip_address": overcloud_environment_variable['parameter_defaults']['VipPortMap']['internal_api']['ip_address'],
            "external_lb_vip_address": overcloud_environment_variable['parameter_defaults']['VipPortMap']['external']['ip_address']
        }
    },
    "mons": {
        "children": [
            "ceph_mon"
        ]
    },
    "mons": {
        "children": [
            "ceph_mon"
        ]
    },
    "neutron_linuxbridge_agent": {
        "children": [
            "neutron_ovs_agent"
        ]
    },
    "neutron_api": {

        "children": [
            "Controller"
        ]
    },
    "heat_api_cfn": {
        "children": [
            "Controller"
        ]
    },
    "undercloud": {
        "children": [
            "Undercloud"
        ],
        "vars": {
            "provisioning_interface": user_maas_variables['undercloud_provisioning_interface'],
            "internal_lb_vip_address": undercloud_tripleo_ansible_inventory['Undercloud']['hosts']['undercloud']['ctlplane_ip'],
            "external_lb_vip_address": undercloud_tripleo_ansible_inventory['Undercloud']['hosts']['undercloud']['external_ip']
        }
    }
}


def list_hosts():
    hosts = {
        "_meta": {
            "hostvars": {}
        },
        "all": {
            "children": []
        }
    }

    for group, group_data in inventory_data.items():
        hosts[group] = {
            "children": group_data.get("children", [])
        }

        if "vars" in group_data:
            hosts[group]["vars"] = group_data["vars"]

    print(json.dumps(hosts, indent=4))


def host_details(hostname):
    host_vars = {}
    for group, group_data in inventory_data.items():
        if hostname in group_data.get("children", []) or group == hostname:
            host_vars.update(group_data.get("vars", {}))

    if host_vars:
        print(json.dumps(host_vars, indent=4))
    else:
        print(f"No details found for host {hostname}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_hosts()
        elif sys.argv[1] == "--host":
            if len(sys.argv) > 2:
                host_details(sys.argv[2])
            else:
                print("Please provide a hostname with --host option")
        else:
            print("Invalid option. Use --list or --host")
    else:
        print("Please provide an option --list or --host")

