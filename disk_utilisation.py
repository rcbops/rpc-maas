#!/usr/bin/env python
"""
Example usage::

    # python disk_utilisation.py
    status okay
    metric disk_utilisation_xvda double 0.00 %
    metric disk_utilisation_xvde double 0.00 %
    
The more drives you have mounted, the more metrics that will be printed.
"""

from maas_common import metric, status_err, status_ok, print_output
import shlex
import subprocess

def utilisation(time):
    output = subprocess.check_output(shlex.split('iostat -x -d %s 2' % time))
    device_lines = output.split('\nDevice:')[-1].strip().split('\n')[1:]
    devices = [d for d in device_lines if not d.startswith('dm-')]
    devices = [d.split() for d in devices]
    utils = [(d[0], d[-1]) for d in devices]
    return utils

if __name__ == '__main__':
    with print_output():
        try:
            utils = utilisation(5)
        except Exception as e:
            status_err(e)
        else:
            status_ok()
            for util in utils:
                metric('disk_utilisation_%s' % util[0], 'double', util[1], '%')
