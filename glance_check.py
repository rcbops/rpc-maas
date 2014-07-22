#!/usr/bin/env python

from glanceclient import Client, exc
from keystoneclient.v2_0 import client
from keystoneclient.openstack.common.apiclient import exceptions
import os
import sys

OS_IMAGE_ENDPOINT = 'http://127.0.0.1:9292'


def set_auth_details():
    auth_details = {'OS_USERNAME': None,
                    'OS_PASSWORD': None,
                    'OS_TENANT_NAME': None,
                    'OS_AUTH_URL': None}

    for key in auth_details.keys():
        if key in os.environ:
            auth_details[key] = os.environ[key]

    return auth_details


def main():
    auth_details = set_auth_details()

    for key, value in auth_details.items():
        if value is None:
            print "status err os.environ['%s'] not set" % key
            sys.exit(1)

    try:
        keystone = client.Client(username=auth_details['OS_USERNAME'],
                                 password=auth_details['OS_PASSWORD'],
                                 tenant_name=auth_details['OS_TENANT_NAME'],
                                 auth_url=auth_details['OS_AUTH_URL'])
    except (exceptions.Unauthorized, exceptions.AuthorizationFailure) as e:
        print "status err %s" % e
        sys.exit(1)

    os_auth_token = keystone.auth_ref['token']['id']

    glance = Client('1', endpoint=OS_IMAGE_ENDPOINT, token=os_auth_token)

    try:
        images = glance.images.findall(status="active")
    except (exc.CommunicationError, exc.HTTPInternalServerError) as e:
        print "status err %s" % e
        sys.exit(1)

    print 'status OK'
    print 'metric glance_active_images uint32 %d' % len(images)

if __name__ == "__main__":
    main()
