import re

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser


AUTH_DETAILS = {
    'OS_USERNAME': None,
    'OS_PASSWORD': None,
    'OS_TENANT_NAME': None,
    'OS_AUTH_URL': None,
    'OS_USER_DOMAIN_NAME': None,
    'OS_PROJECT_DOMAIN_NAME': None,
    'OS_PROJECT_NAME': None,
    'OS_IDENTITY_API_VERSION': None,
    'OS_AUTH_VERSION': None,
    'OS_ENDPOINT_TYPE': None,
    'OS_API_INSECURE': True,
    'OS_INSECURE': True,
    'OS_REGION_NAME': 'RegionOne'
}


def get_auth_details():
    auth_details = AUTH_DETAILS
    pattern = re.compile(
        '^(?:export\s)?(?P<key>\w+)(?:\s+)?=(?:\s+)?(?P<value>.*)$'
    )

    try:
        with open('/root/openrc') as openrc:
            for line in openrc:
                match = pattern.match(line)
                if match is None:
                    continue
                k = match.group('key')
                v = match.group('value')
                if k in auth_details and auth_details[k] is None:
                    auth_details[k] = v
    except IOError as e:
        if e.errno != errno.ENOENT:
            status_err(str(e), m_name='maas_keystone')
        # no openrc file, so we try the environment
        for key in auth_details.keys():
            auth_details[key] = os.environ.get(key)

    for key in auth_details.keys():
        if auth_details[key] is None:
            status_err('%s not set' % key, m_name='maas_keystone')

    return auth_details


def main():
    config = ConfigParser.RawConfigParser()
    config.add_section('ALL')
    for k, v in get_auth_details().items():
        key = k.lower().lstrip('os_')
        config.set('DEFAULT', key, str(v).strip("'").strip('"'))

    with open('/root/monitorstack.ini', 'w') as f:
        config.write(f)

if __name__ == '__main__':
    main()
