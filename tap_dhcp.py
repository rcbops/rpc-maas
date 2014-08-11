import re
import subprocess

from maas_common import metric, metric_bool, status_ok, status_err


def get_namespace_list():
    """Retrieve the list of DHCP namespaces."""
    namespaces = subprocess.check_output(['ip', 'netns', 'list']).split()
    ns_list = list(filter(lambda n: n.startswith('qdhcp-'), namespaces))

    if not ns_list:
        status_err('no dhcp namespaces on this host')

    return ns_list


def get_interfaces_for(namespace):
    """Retrieve the list of interfaces inside a namespace."""
    return subprocess.check_output([
        'ip', 'netns', 'exec', namespace, 'ip', 'a'
    ]).split('\n')


def get_bridges():
    """Retrieve a list of bridges from brctl."""
    brctl = subprocess.check_output(['brctl', 'show']).split('\n')
    return [
        i.split('\t')[0] for i in brctl
        if i and not i.startswith((' ', '\t', 'bridge name'))
    ]


def generate_network_device_details(bridges):
    """Generate a list of network device details from ip."""
    ip = subprocess.check_output(['ip', 'a']).split('\n')
    ignored_devices = set(['lo'] + bridges)
    for line in ip:
        if line.startswith(' '):
            continue

        (_, name, details) = line.split(': ')
        if name in ignored_devices:
            continue

        yield details


def check_for_disconnected_veth_pairs():
    """Return True if there are disconnected pairs else False."""
    bridges = get_bridges()
    return any(
        all(bridge_name not in detail for bridge_name in bridges)
        for detail in generate_network_device_details(bridges)
    )


def main():
    TAP = re.compile('^\d+: .*state [A-Z]+$')
    LOOP = re.compile('^\d+: lo')
    namespaces = get_namespace_list()

    interfaces = ((n, get_interfaces_for(n)) for n in namespaces)
    too_many_taps = []
    for namespace, interface_list in interfaces:
        # Filter down to the output of ip a that looks like 1: lo
        named_interfaces = filter(lambda i: TAP.match(i), interface_list)
        num_taps = len([i for i in named_interfaces if not LOOP.match(i)])
        if num_taps != 1:
            too_many_taps.append(
                ('namespace_{0}'.format(namespace), num_taps)
            )

    number_of_namespaces = len(too_many_taps)
    status_ok()  # We were able to check the number of interfaces after all
    # We should alarm on the following condition, i.e., if it isn't 0.
    metric('namespaces_with_more_than_one_tap', 'int32', number_of_namespaces)
    if number_of_namespaces > 0:
        for (name, number) in too_many_taps:
            metric(name, 'uint32', number)

    metric_bool('disconnected_veth_pair_exists',
                check_for_disconnected_veth_pairs())


if __name__ == '__main__':
    main()
