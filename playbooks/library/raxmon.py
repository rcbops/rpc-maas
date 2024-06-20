
# Copyright 2017, Rackspace US, Inc.
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

import configparser
import subprocess
from ansible.module_utils.basic import *  # noqa: ignore=H303


DOCUMENTATION = """
---
module: raxmon
short_description:
  - A module for preparing a node for Rackspace Cloud Monitoring
description:
  - This module is written for rpc-openstack's rpc_maas role specifically to
    prepare a node for Rackspace Cloud Monitoring by a) assigning an agent
    to an entity and b) creating an agent token.
options:
  cmd:
    description: The command to run
    choices = [ 'assign_agent_to_entity', 'create_agent_token',
                'delete_agent_token', 'delete_entity']
    required: true
  entity:
    description: The label of the entity to operate against
    required: true
  venv_bin:
    description: The path to the venv where rackspace-monitoring is installed
    required: false
  raxmon_cfg:
    description: The path to the raxmon configuration file
    required: false
    default: /root/.raxrc
"""

EXAMPLES = """
raxmon:
  cmd: assign_agent_to_entity
  entity: controller1
  venv_bin: /openstack/venvs/maas-r14.1.0rc1/bin/
  create_entity_if_not_exists: true

raxmon:
  cmd: create_agent_token
  entity: controller1
  venv_bin: /openstack/venvs/maas-r14.1.0rc1/bin/

raxmon:
  cmd: create_private_zone
  entity: controller1
  venv_bin: /openstack/venvs/maas-r14.1.0rc1/bin/

raxmon:
  cmd: delete_agent_token
  entity: controller1
  venv_bin: /openstack/venvs/maas-r14.1.0rc1/bin/

raxmon:
  cmd: delete_entity
  entity: controller1
  venv_bin: /openstack/venvs/maas-r14.1.0rc1/bin/

raxmon:
  cmd: delete_private_zone
  entity: controller1
  venv_bin: /openstack/venvs/maas-r14.1.0rc1/bin/
"""

RETURN = """
id:
  description:
    - The ID of the entity's agent token, returned when cmd=create_agent_token
  returned: success
  type: id
"""


def _get_agent_tokens(conn, entity):
    agent_tokens = []
    for a in conn.list_agent_tokens():
        if a.label == entity:
            agent_tokens.append(a)
    return agent_tokens


def _get_conn(get_driver, provider_cls, raxmon_cfg):
    cfg = configparser.RawConfigParser()
    cfg.read(raxmon_cfg)
    driver = get_driver(provider_cls.RACKSPACE)
    try:
        user = cfg.get('credentials', 'username')
        api_key = cfg.get('credentials', 'api_key')
        conn = driver(user, api_key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        url = cfg.get('api', 'url')
        token = cfg.get('api', 'token')
        conn = driver(None, None, ex_force_base_url=url,
                      ex_force_auth_token=token)
    return conn


def _get_entities(conn, entity, create_entity_if_not_exists=False):
    entities = []
    for e in conn.list_entities():
        if e.label == entity:
            entities.append(e)
    # create entity if needed
    if create_entity_if_not_exists and len(entities) == 0:
        created = conn.create_entity(label=entity)
        entities = [created]
    return entities


def assign_agent_to_entity(module, conn, entity, create_entity_if_not_exists):
    entities = _get_entities(conn, entity, create_entity_if_not_exists)
    entities_count = len(entities)
    if entities_count == 0:
        msg = "Zero entities with the label %s exist. Entities should be " \
              "created as part of the hardware provisioning process, if " \
              "missing, please consult the internal documentation for " \
              "associating one with the device." % entity
        module.fail_json(msg=msg)
    elif entities_count == 1:
        if entities[0].label == entities[0].agent_id:
            module.exit_json(change=False)
        else:
            conn.update_entity(entities[0], {'agent_id': entity})
            module.exit_json(changed=True)
    elif entities_count > 1:
        msg = "Entity count of %s != 1 for entity with the label %s. Reduce " \
              "the entity count to one by deleting or re-labelling the " \
              "duplicate entities." % (entities_count, entity)
        module.fail_json(msg=msg)


def create_agent_token(module, conn, entity):
    agent_tokens = _get_agent_tokens(conn, entity)
    agent_tokens_count = len(agent_tokens)
    if agent_tokens_count == 0:
        module.exit_json(
            changed=True,
            id=conn.create_agent_token(label=entity).id
        )
    elif agent_tokens_count == 1:
        module.exit_json(
            changed=False,
            id=agent_tokens[0].id
        )
    elif agent_tokens_count > 2:
        msg = "Agent token count of %s > 1 for entity with " \
              "the label %s" % (agent_tokens_count, entity)
        module.fail_json(msg=msg)


def create_private_zone(module, conn, entity):
    private_zones = [z for z in conn.list_monitoring_zones()
                     if z.label == entity]

    # Create zone if one doesnt exist
    if len(private_zones) == 0:
        module.exit_json(
            changed=True,
            id=conn.create_monitoring_zone(label=entity).id
        )
    # Exit if the zone already exists
    elif len(private_zones) == 1:
        module.exit_json(
            changed=False,
            id=private_zones[0].id
        )


def delete_private_zone(module, conn, entity):
    private_zones = [z for z in conn.list_monitoring_zones()
                     if z.label == entity]
    msg = ''

    if len(private_zones) > 0:
        for zone in private_zones:
            try:
                conn.delete_monitoring_zone(zone)
            except Exception as e:
                msg += "Deleting private zone for %s failed. Reason: %s" % (
                    zone.label,
                    str(e.message)
                )

    if len(msg) > 0:
        module.fail_json(msg=msg)
    else:
        module.exit_json(changed=True)


def delete_agent_token(module, conn, entity):
    agent_tokens = _get_agent_tokens(conn, entity)
    msg = ''
    for token in agent_tokens:
        try:
            conn.delete_agent_token(token)
        except Exception as e:
            msg += "Deleting agent token for %s failed. Reason: %s" % (
                token.label,
                str(e.message)
            )
    if len(msg) > 0:
        module.fail_json(msg=msg)
    else:
        module.exit_json(changed=True)


def delete_entity(module, conn, entity):
    entities = _get_entities(conn, entity)
    msg = ''
    for entity in entities:
        try:
            conn.delete_entity(entity)
        except Exception as e:
            msg += "Deleting entity: %s failed. Reason: %s" % (
                entity.label,
                str(e.message)
            )
    if len(msg) > 0:
        module.fail_json(msg=msg)
    else:
        module.exit_json(changed=True)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cmd=dict(
                choices=['assign_agent_to_entity', 'create_agent_token',
                         'create_private_zone', 'delete_private_zone',
                         'delete_agent_token', 'delete_entity'],
                required=True
            ),
            entity=dict(required=True),
            venv_bin=dict(),
            create_entity_if_not_exists=dict(
                type='bool',
                default=False
            ),
            raxmon_cfg=dict(default='/root/.raxrc')
        )
    )

    if module.params['venv_bin']:
        activate_this = '%s/activate' % (module.params['venv_bin'])
        subprocess.call(['bash', '-c', f'source {activate_this}'])

    # We place these imports after we activate the virtualenv to ensure we're
    # importing the correct libraries
    from rackspace_monitoring.providers import get_driver
    from rackspace_monitoring.types import Provider
    import libcloud.security

    # Provide the ability to enable or disable SSL certificate verification
    # with raxmon
    cfg = configparser.RawConfigParser()
    cfg.read(module.params['raxmon_cfg'])
    verify_ssl = cfg.get('ssl', 'verify')
    if verify_ssl == 'true':
        verify_ssl = True
    else:
        verify_ssl = False
    libcloud.security.VERIFY_SSL_CERT = verify_ssl

    conn = _get_conn(get_driver, Provider, module.params['raxmon_cfg'])

    if module.params['cmd'] == 'assign_agent_to_entity':
        assign_agent_to_entity(module, conn, module.params['entity'],
                               module.params['create_entity_if_not_exists'])
    elif module.params['cmd'] == 'create_agent_token':
        create_agent_token(module, conn, module.params['entity'])
    elif module.params['cmd'] == 'create_private_zone':
        create_private_zone(module, conn, module.params['entity'])
    elif module.params['cmd'] == 'delete_agent_token':
        delete_agent_token(module, conn, module.params['entity'])
    elif module.params['cmd'] == 'delete_entity':
        delete_entity(module, conn, module.params['entity'])
    elif module.params['cmd'] == 'delete_private_zone':
        delete_private_zone(module, conn, module.params['entity'])


if __name__ == '__main__':
    main()
