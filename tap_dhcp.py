import re
import subprocess

from maas_common import metric, status_ok, status_err


def get_namespace_list():
    """Retrieve the list of DHCP namespaces."""
    return subprocess.check_output(['ip', 'netns', 'list']).split()


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
    metrics = []
    for namespace, interface_list in interfaces:
        # Filter down to the output of ip a that looks like 1: lo
        named_interfaces = filter(lambda i: TAP.match(i), interface_list)
        num_taps = len([i for i in named_interfaces if not LOOP.match(i)])
        if num_taps != 1:
            metrics.append(('namespace_{0}'.format(namespace), num_taps))

    if len(metrics) > 0:
        status_err('a namespace had an unexpected number of TAPs present')
        for (name, number) in metrics:
            metric(name, 'uint32', number)

    status_ok()


if __name__ == '__main__':
    main()
