#!/usr/bin/env python

import sys
import time

from heatclient.client import Client
from keystoneclient import session as kssession
from keystoneclient.auth import token_endpoint
from maas_common import get_auth_details
from maas_common import get_auth_ref
from maas_common import status_err

STATUS_COMPLETE = 'COMPLETE'
STATUS_FAILED = 'FAILED'
STATUS_IN_PROGRESS = 'IN_PROGRESS'
ORCHESTRATION = 'orchestration'
PUBLIC_URL = 'publicURL'


def check_availability(auth_ref):
    """Check the availability of the Heat Orchestration API.

    :param auth_ref: A Keystone auth token reference for use in querying Heat

    Metrics include stacks built from either heat or cfn templates.
    Outputs metrics on current status of Heat and time elapsed during query.
    Outputs an error status if any error occurs querying Heat.
    Exits with 0 if Heat is available and responds with 200, otherwise 1.
    """
    keystone = maas_common.get_keystone_client(auth_ref)
    if keystone is None:
        status_err('Unable to obtain valid keystone client, cannot proceed')

    auth_details = get_auth_details()
    keystone_session = kssession.Session(verify=True)
    heat_endpoint = keystone.service_catalog.url_for(
        service_type=ORCHESTRATION, endpoint_type=PUBLIC_URL)
    auth_token_id = keystone.auth_ref['token']['id']
    keystone_auth = token_endpoint.Token(heat_endpoint, auth_token_id)
    kwargs = {
        'auth_url': auth_details['OS_AUTH_URL'],
        'session': keystone_session,
        'auth': keystone_auth,
        'service_type': ORCHESTRATION,
        'endpoint_type': PUBLIC_URL,
        'username': auth_details['OS_USERNAME'],
        'password': auth_details['OS_PASSWORD'],
        'include_pass': True
    }
    heat = Client('1', heat_endpoint, **kwargs)
    complete, failed, in_progress = 0, 0, 0

    start_at = time.time()
    try:
        for stack in heat.stacks.list():
            if STATUS_COMPLETE == stack.status:
                complete += 1
            if STATUS_FAILED == stack.status:
                failed += 1
            if STATUS_IN_PROGRESS == stack.status:
                in_progress += 1
    except Exception as e:
        status_err(e)
    elapsed_ms = (time.time() - start_at) * 1000

    print 'status heat api success'
    print 'metric heat_active_stacks uint32 {0}'.format(complete)
    print 'metric heat_killed_stacks uint32 {0}'.format(failed)
    print 'metric heat_queued_stacks uint32 {0}'.format(in_progress)
    print 'metric heat_response_ms double {0}'.format(elapsed_ms)


def main():
    check_availability(get_auth_ref())

if __name__ == "__main__":
    main()
