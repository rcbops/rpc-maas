#!/usr/bin/env python
"""Render the real MaaS variables using Ansible's templating engine."""

from pathlib import Path
import unittest

from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar
import yaml


class ForbiddenHostVars(dict):
    def __getitem__(self, key):
        raise AssertionError('Bond detection must not reload hostvars')


class BondDetectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1]
        with (path / 'playbooks/vars/maas.yml').open() as source:
            cls.maas_vars = yaml.safe_load(source)

    def render(self, interfaces, facts, override=None):
        variables = dict(self.maas_vars)
        variables.update(ansible_interfaces=interfaces, ansible_facts=facts,
                         inventory_hostname='controller',
                         hostvars=ForbiddenHostVars())
        if override is not None:
            variables['maas_bonding_interfaces'] = override
        return Templar(loader=DataLoader(), variables=variables).template(
            '{{ maas_bonding_interfaces }}')

    def test_standard_bonds(self):
        self.assertEqual(self.render(
            ['eth0', 'bond0', 'bond1'],
            {'eth0': {'type': 'ether'}, 'bond0': {'type': 'bonding'},
             'bond1': {'type': 'bonding'}}), ['bond0', 'bond1'])

    def test_custom_bonds_and_order(self):
        self.assertEqual(self.render(
            ['storage', 'bond42', 'bond0'],
            {name: {'type': 'bonding'}
             for name in ['bond0', 'bond42', 'storage']}),
            ['storage', 'bond42', 'bond0'])

    def test_hyphenated_name(self):
        self.assertEqual(self.render(
            ['bond-storage'], {'bond_storage': {'type': 'bonding'}}),
            ['bond-storage'])

    def test_missing_and_incomplete_facts(self):
        self.assertEqual(self.render(
            ['missing', 'empty', 'no_type'],
            {'empty': {}, 'no_type': {'device': 'no_type'}}), '')

    def test_non_bond_named_bond0(self):
        self.assertEqual(self.render(
            ['bond0'], {'bond0': {'type': 'ether'}}), '')

    def test_empty_interfaces(self):
        # Ansible converts the existing YAML null to an empty string.
        self.assertEqual(self.render([], {}), '')

    def test_explicit_override(self):
        self.assertEqual(self.render([], {}, ['custom']), ['custom'])

    def test_many_interfaces_without_hostvars_access(self):
        interfaces = ['tap%d' % index for index in range(5000)] + ['bond42']
        facts = {name: {'type': 'ether'} for name in interfaces}
        facts['bond42'] = {'type': 'bonding'}
        self.assertEqual(self.render(interfaces, facts), ['bond42'])


if __name__ == '__main__':
    unittest.main()
