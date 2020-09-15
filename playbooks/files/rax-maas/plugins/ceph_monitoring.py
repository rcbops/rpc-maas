#!/usr/bin/env python

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
import json
from maas_common import metric_bool
from maas_common import metric
from maas_common import MaaSException
from maas_common import status_ok
from maas_common import print_output
import requests
import subprocess


STATUSES = {'HEALTH_OK': 2, 'HEALTH_WARN': 1, 'HEALTH_ERR': 0}
IGNORE_CHECKS = ['OSDMAP_FLAGS', 'OBJECT_MISPLACED']

# See https://docs.ceph.com/docs/master/rados/operations/health-checks
# for details on each. We had to break these down into sections as each
# check has a max of 50 allowed metrics.
DETAILED_CHECKS = {
    'mon': [
        'MON_DOWN',
        'MON_CLOCK_SKEW',
        'MON_MSGR2_NOT_ENABLED',
        'MON_DISK_LOW',
        'MON_DISK_CRIT',
        'MON_DISK_BIG',
    ],
    'mgr': [
        'MGR_DOWN',
        'MGR_MODULE_DEPENDENCY',
        'MGR_MODULE_ERROR',
    ],
    'osds': [
        'OSD_DOWN',
        'OSD_DOWN',
        'OSD_HOST_DOWN',
        'OSD_ROOT_DOWN',
        'OSD_ORPHAN',
        'OSD_OUT_OF_ORDER_FULL',
        'OSD_FULL',
        'OSD_BACKFILLFULL',
        'OSD_NEARFULL',
        'OSDMAP_FLAGS',
        'OSD_FLAGS',
        'OLD_CRUSH_TUNABLES',
        'OLD_CRUSH_STRAW_CALC_VERSION',
        'CACHE_POOL_NO_HIT_SET'
        'OSD_NO_SORTBITWISE',
        'BLUEFS_SPILLOVER',
        'BLUEFS_AVAILABLE_SPACE',
        'BLUEFS_LOW_SPACE',
        'BLUESTORE_FRAGMENTATION',
        'BLUESTORE_LEGACY_STATFS',
        'BLUESTORE_NO_PER_POOL_OMAP',
        'BLUESTORE_DISK_SIZE_MISMATCH',
        'BLUESTORE_NO_COMPRESSION',
        'BLUESTORE_SPURIOUS_READ_ERRORS',
    ],
    'device_health': [
        'DEVICE_HEALTH',
        'DEVICE_HEALTH_IN_USE',
        'DEVICE_HEALTH_TOOMANY',
    ],
    'data_health': [
        'PG_AVAILABILITY',
        'PG_DEGRADED',
        'PG_RECOVERY_FULL',
        'PG_BACKFILL_FULL',
        'PG_DAMAGED',
        'OSD_SCRUB_ERRORS',
        'LARGE_OMAP_OBJECTS',
        'CACHE_POOL_NEAR_FULL',
        'TOO_FEW_PGS',
        'POOL_PG_NUM_NOT_POWER_OF_TWO',
        'POOL_TOO_FEW_PGS',
        'TOO_MANY_PGS',
        'POOL_TARGET_SIZE_BYTES_OVERCOMMITTED',
        'POOL_HAS_TARGET_SIZE_BYTES_AND_RATIO',
        'TOO_FEW_OSDS',
        'SMALLER_PGP_NUM',
        'MANY_OBJECTS_PER_PG',
        'POOL_APP_NOT_ENABLED',
        'POOL_FULL',
        'POOL_NEAR_FULL',
        'OBJECT_MISPLACED',
        'OBJECT_UNFOUND',
        'SLOW_OPS',
        'PG_NOT_SCRUBBED',
        'PG_NOT_DEEP_SCRUBBED',
        'PG_SLOW_SNAP_TRIMMING',
    ],
    'misc': [
        'RECENT_CRASH',
        'TELEMETRY_CHANGED',
        'AUTH_BAD_CAPS',
        'OSD_NO_DOWN_OUT_INTERVAL',
    ],
}


def check_command(command, container_name=None, deploy_osp=False):
    if container_name:
        container_command = ['lxc-attach',
                             '-n',
                             container_name,
                             '--',
                             'bash',
                             '-c']
        container_command.append("{}".format(' '.join(command)))
        if deploy_osp:
            container_command = []
            container_command.extend(command)
        command = [str(i) for i in container_command]
    output = subprocess.check_output(command, stderr=subprocess.STDOUT)
    lines = output.strip().split('\n')
    return json.loads(lines[-1])


def get_ceph_rgw_hostcheck(rgw_address, container_name=None):
    try:
        sc = requests.get(rgw_address, verify=False).status_code
        if (sc >= 200) and (sc < 300):
            status_code = 2
        else:
            status_code = 1
    except requests.exceptions.ConnectionError:
        status_code = 0
    return status_code


def get_ceph_status(client, keyring, fmt='json', container_name=None,
                    deploy_osp=False):
    return check_command(('ceph', '--format', fmt, '--name', client,
                          '--keyring', keyring, 'status'),
                         container_name=container_name,
                         deploy_osp=deploy_osp)


def get_local_osd_info(osd_ref, fmt='json', container_name=None,
                       deploy_osp=False):
    return check_command(
        ('ceph', '--format', fmt, 'daemon', osd_ref, 'status'),
        container_name=container_name,
        deploy_osp=deploy_osp
    )


def get_mon_statistics(client=None, keyring=None, host=None,
                       container_name=None, deploy_osp=False):
    ceph_status = get_ceph_status(client=client,
                                  keyring=keyring,
                                  container_name=container_name,
                                  deploy_osp=deploy_osp)
    mon = [m for m in ceph_status['monmap']['mons']
           if m['name'] == host]
    mon_in = mon[0]['rank'] in ceph_status['quorum']
    metric_bool('mon_in_quorum', mon_in)


def get_health_checks(client=None, keyring=None, section=None,
                      container_name=None, deploy_osp=False):
    metrics = []

    ceph_status = get_ceph_status(client=client,
                                  keyring=keyring,
                                  container_name=container_name,
                                  deploy_osp=deploy_osp)

    # Go through the detailed health checks and generate metrics
    # for each based on the given section
    for curcheck in DETAILED_CHECKS[section]:
        if curcheck in ceph_status['health']['checks']:
            severity = ceph_status['health']['checks'][curcheck]['severity']
            metrics.append({'name': curcheck,
                            'type': 'uint32',
                            'value': STATUSES[severity]})
        else:
            metrics.append({'name': curcheck,
                            'type': 'uint32',
                            'value': STATUSES['HEALTH_OK']})

    # Submit gathered metrics
    for m in metrics:
        metric(m['name'], m['type'], m['value'])


def get_rgw_checkup(client, keyring=None, rgw_address=None,
                    container_name=None, deploy_osp=False):
    rgw_status = get_ceph_rgw_hostcheck(rgw_address,
                                        container_name=container_name)
    metric('rgw_up', 'uint32', rgw_status)


def get_osd_statistics(client=None, keyring=None, osd_id=None,
                       container_name=None, deploy_osp=False):
    osd_ref = "osd.%s" % osd_id
    try:
        osd_info = get_local_osd_info(
            osd_ref, container_name=container_name, deploy_osp=deploy_osp
        )
    except Exception:
        msg = 'The OSD ID %s does not exist.' % osd_id
        raise MaaSException(msg)
    else:
        state = 1 if osd_info.get('state', '') == 'active' else 0
        metric_name = '_'.join((osd_ref, 'up'))
        metric_bool(metric_name, state)


def get_cluster_statistics(client=None, keyring=None, container_name=None,
                           deploy_osp=False):
    metrics = []

    ceph_status = get_ceph_status(client=client,
                                  keyring=keyring,
                                  container_name=container_name,
                                  deploy_osp=deploy_osp)
    # Get overall cluster health
    # For luminous+ this is the ceph_status.health.status
    # For < Luminous this is the ceph_status.health.overall_status
    # SLM: 'overall_status' exists along with 'status' for luminous.
    #      It will be HEALTH_WARN while 'status' will be HEALTH_OK.
    #      The following should work for all with the newer overriding
    #      the older if both exist.
    ceph_health_status = 'HEALTH_ERR'
    if 'overall_status' in ceph_status['health']:
        ceph_health_status = ceph_status['health']['overall_status']
    if 'status' in ceph_status['health']:
        ceph_health_status = ceph_status['health']['status']

    # Ignore checks. Quick fix from ceph admin request.
    if ceph_health_status != 'HEALTH_OK':
        ignore = True
        for curcheck in ceph_status['health']['checks']:
            if curcheck not in IGNORE_CHECKS:
                ignore = False
                break
        if ignore:
            ceph_health_status = 'HEALTH_OK'

    metrics.append({
        'name': 'cluster_health',
        'type': 'uint32',
        'value': STATUSES[ceph_health_status]})

    # Collect epochs for the mon and osd maps
    metrics.append({'name': "monmap_epoch",
                    'type': 'uint32',
                    'value': ceph_status['monmap']['epoch']})
    metrics.append({'name': "osdmap_epoch",
                    'type': 'uint32',
                    'value': ceph_status['osdmap']['osdmap']['epoch']})

    # Collect OSDs per state
    osds = {'total': ceph_status['osdmap']['osdmap']['num_osds'],
            'up': ceph_status['osdmap']['osdmap']['num_up_osds'],
            'in': ceph_status['osdmap']['osdmap']['num_in_osds']}
    for k in osds:
        metrics.append({'name': 'osds_%s' % k,
                        'type': 'uint32',
                        'value': osds[k]})

    # Collect cluster size & utilisation
    metrics.append({'name': 'osds_kb_used',
                    'type': 'uint64',
                    'value': ceph_status['pgmap']['bytes_used'] / 1024})
    metrics.append({'name': 'osds_kb_avail',
                    'type': 'uint64',
                    'value': ceph_status['pgmap']['bytes_avail'] / 1024})
    metrics.append({'name': 'osds_kb',
                    'type': 'uint64',
                    'value': ceph_status['pgmap']['bytes_total'] / 1024})

    # Collect num PGs and num healthy PGs
    pgs = {'total': ceph_status['pgmap']['num_pgs'], 'active_clean': 0}
    for state in ceph_status['pgmap']['pgs_by_state']:
        if state['state_name'] == 'active+clean':
            pgs['active_clean'] = state['count']
            break
    for k in pgs:
        metrics.append({'name': 'pgs_%s' % k,
                        'type': 'uint32',
                        'value': pgs[k]})

    # Submit gathered metrics
    for m in metrics:
        metric(m['name'], m['type'], m['value'])


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name',
                        required=True,
                        help='Ceph client name')
    parser.add_argument('--deploy_osp',
                        action='store_true',
                        default=False,
                        help='Option for extending into OSP environments')
    parser.add_argument('--keyring',
                        required=True,
                        help='Ceph client keyring')
    parser.add_argument('--container-name',
                        required=False,
                        default=None,
                        help='Ceph Container Name')

    subparsers = parser.add_subparsers(dest='subparser_name')

    parser_mon = subparsers.add_parser('mon')
    parser_mon.add_argument('--host', required=True, help='Mon hostname')

    parser_osd = subparsers.add_parser('osd')
    parser_osd.add_argument('--osd_id', required=True, type=str,
                            help='A single OSD ID')
    parser_rgw = subparsers.add_parser('rgw')
    parser_rgw.add_argument('--rgw_address', required=True,
                            help='RGW address in form proto://ip_addr:port/')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')

    parser_mon = subparsers.add_parser('health_checks')
    # From https://docs.ceph.com/docs/master/rados/operations/health-checks
    parser_mon.add_argument('--section',
                            required=True,
                            help='(mon,mgr,osds,device_health,data_health \
                            or misc)')

    subparsers.add_parser('cluster')
    return parser.parse_args()


def main(args):
    get_statistics = {'cluster': get_cluster_statistics,
                      'mon': get_mon_statistics,
                      'rgw': get_rgw_checkup,
                      'osd': get_osd_statistics,
                      'health_checks': get_health_checks}
    kwargs = {'client': args.name, 'keyring': args.keyring}
    if args.subparser_name == 'osd':
        kwargs['osd_id'] = args.osd_id
    if args.subparser_name == 'mon':
        kwargs['host'] = args.host
    if args.subparser_name == 'rgw':
        kwargs['rgw_address'] = args.rgw_address
    if args.subparser_name == 'health_checks':
        kwargs['section'] = args.section

    kwargs['container_name'] = args.container_name
    kwargs['deploy_osp'] = args.deploy_osp

    get_statistics[args.subparser_name](**kwargs)
    status_ok(m_name='maas_ceph')


if __name__ == '__main__':
    args = get_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
