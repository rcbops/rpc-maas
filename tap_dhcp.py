import re
import subprocess

from maas_common import metric, status_ok, status_err


def get_namespace_list():
    """Retrieve the list of DHCP namespaces."""
    namespaces = subprocess.check_output(['ip', 'netns', 'list']).split()
    return list(filter(lambda n: n.startswith('qdhcp-'), namespaces))


def get_interfaces_for(namespace):
    """Retrieve the list of interfaces inside a namespace."""
    return subprocess.check_output([
        'ip', 'netns', 'exec', namespace, 'ip', 'a'
    ]).split('\n')


def main():
    TAP = re.compile('^\d+: .*state [A-Z]+$')
    LOOP = re.compile('^\d+: lo')
    namespaces = get_namespace_list()
    if not namespaces:
        status_err('no dhcp namespaces on this host')

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
        status_err('a namespace had an unexpected number of TAPs present')
        for (name, number) in too_many_taps:
            metric(name, 'uint32', number)


if __name__ == '__main__':
    main()
