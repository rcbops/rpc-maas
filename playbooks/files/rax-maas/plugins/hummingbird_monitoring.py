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
import maas_common
import pprint
import swiftclient

from maas_common import get_auth_details
from maas_common import get_keystone_client
from maas_common import get_keystone_client
from maas_common import get_auth_ref
from maas_common import get_endpoint_url_for_service


def main():
    responses = {
        'put_container': 200,
        'put_object': 200,
        'get_object': 200,
        'delete_object': 200,
    }
    contents = "TESTCONTENTS"

    auth_ref = get_auth_ref()
    keystone = get_keystone_client(auth_ref)
    endpoint = get_endpoint_url_for_service("object-store", auth_ref)
    conn = swiftclient.client.Connection(
        preauthurl=endpoint,
        preauthtoken=keystone.auth_token,
        retries=0,
    )

    try:
        conn.put_container("hummingbird-maas")
    except swiftclient.client.ClientException as e:
        responses['put_container'] = e.http_status

    try:
        etag = conn.put_object("hummingbird-maas", "test-object", contents)
    except swiftclient.client.ClientException as e:
        responses['put_object'] = e.http_status

    try:
        headers, body = conn.get_object("hummingbird-maas", "test-object")
        if body != contents:
            responses['get_object'] = 400
    except swiftclient.client.ClientException as e:
        responses['get_object'] = e.http_status

    try:
        conn.delete_object("hummingbird-maas", "test-object")
    except swiftclient.client.ClientException as e:
        responses['delete_object'] = e.http_status

    maas_common.status_ok(m_name='maas_hummingbird')
    for k, v in responses.iteritems():
        maas_common.metric(k, 'uint32', v)


if __name__ == '__main__':
    with maas_common.print_output():
        main()

