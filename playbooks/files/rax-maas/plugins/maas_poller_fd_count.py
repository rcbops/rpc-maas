#!/usr/bin/env python3
#
# Copyright 2015, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import psutil

from maas_common import metric
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def _get_poller_proc(name="rackspace-monitoring-poller"):
    """Return the process relating to the running poller

    This reports an appropriate status if either zero or
    more than one pollers are found.

    Returns None when more than one poller is found.
    """
    procs = filter(lambda proc: proc.name() == name, psutil.process_iter())

    metric_name = "maas_poller"

    poller_count = len(procs)
    if poller_count > 1:
        status_err("Found %d %s instances" % (poller_count, name),
                   m_name=metric_name)
    elif poller_count == 0:
        status_err("No %s found" % name,
                   m_name=metric_name)
    else:
        status_ok(m_name=metric_name)

    return procs[0] if poller_count == 1 else None


def get_poller_fd_details():
    """Generate metrics for the poller's file descriptor usage"""
    proc = _get_poller_proc()
    if proc is None:
        return

    metric("maas_poller_fd_count", "uint32", proc.num_fds())

    # rlimit returns soft and hard limits, but only use hard
    _, hard_limit = proc.rlimit(psutil.RLIMIT_NOFILE)
    metric("maas_poller_fd_max", "uint32", hard_limit)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check poller file descriptor usage")

    parser.add_argument("--telegraf-output",
                        action="store_true",
                        default=False,
                        help="Set the output format to telegraf")

    args = parser.parse_args()

    with print_output(print_telegraf=args.telegraf_output):
        get_poller_fd_details()
