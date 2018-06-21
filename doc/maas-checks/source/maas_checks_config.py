import collections
import itertools
try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib
import re

from ansible.plugins.filter import core as ansible_filters
from ansible.plugins.test import core as ansible_tests
import jinja2
import jinja2.meta
import yaml


PLAYBOOKS_DIR = "playbooks/"
TEMPLATES_DIR = "{root}/templates/rax-maas".format(root=PLAYBOOKS_DIR)
VARS_DIR = "{root}/vars".format(root=PLAYBOOKS_DIR)

# NOTE: This regex includes the outer parenthesis. This is at least
# consistent in that we can always strip the first and last charaters
# off, but consider improving this to save a string manipulation step.
CRITERIA = re.compile("\\(([^()]*|\\([^()]*\\))*\\)")

# The following template files are not processed by this script.
IGNORED_TEMPLATES = (
    "checks_base.yaml.j2", # base template, nothing in there to use.
    "maas_rally.yaml.j2", # not check related
    "rally_deployment.yaml.j2", # not check related
    "clouds.yaml.j2", # not check related
    )


class SilentUndefined(jinja2.Undefined):

    # For Python 2
    def __unicode__(self):
        """If this gets unicode'ed, return the undefined version back.

        We need this to remain undefined when searching for the
        undefined criteria.
        """
        return u"{{ %s }}" % self._undefined_name

    # For Python 3
    def __str__(self):
        """If this gets str'ed, return the undefined version back.

        We need this to remain undefined when searching for the
        undefined criteria.
        """
        return "{{ %s }}" % self._undefined_name

    def _return_name(self, *args, **kwargs):
        """Return the name as a string when it's undefined"""
        return str(self._undefined_name)

    # For any access, return the string.
    __getitem__ = __getattr__ = _return_name

    # rabbitmq_status.yaml.j2 divides a threshold by a time
    # so we need to handle that. I'm not aware of how we can *actually*
    # handle the division while rendering the template. This will only
    # give back the actual value of the numerator.
    # TODO(briancurtin): see if we can do actual division
    def __truediv__(self, value):
        return "{{ %s }}" % self._undefined_name


class RemappingLoader(yaml.Loader):

    def construct_mapping(self, node, deep=False):
        """Return a mapping between key and value nodes

        This overrides the default construct_mapping to handle
        the case when we're parsing Jinja template replacement
        fields that are for integers, which are bare brackets,
        e.g., {{ blah }} versus "{{ blah }}". When pyyaml tries
        to read {{ blah }} with no quotes, it reads that as a
        mapping, then tries to use the mapping as a key in yet
        another mapping. Since {{ blah }} isn't hashable, this fails.
        However, since we don't really want that and instead we want
        this as a string, convert any unhashable keys to ScalarNodes
        and try it again. We want the string version anyway since
        we're only looking for what the variable name is.
        """
        if not isinstance(node, yaml.MappingNode):
            raise ConstructorError(None, None,
                    "expected a mapping node, but found %s" % node.id,
                    node.start_mark)

        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)

            if not isinstance(key, collections.Hashable):
                # If we can't hash it, take the value we need out of the
                # mapping and convert it to a ScalarNode, then retry.
                old_value = key_node.value[0][0].value
                new_node = yaml.ScalarNode(tag="tag:yaml.org,2002:str",
                                           value='"{{ %s }}"' % old_value)

                key = self.construct_object(new_node, deep=deep)

            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value

        return mapping


def _get_defaults(root, vars_dir=VARS_DIR):
    """Return a dictionary of variables

    This returns *all* variables configured for use in the
    rpc-maas playbooks, not just those relating to the monitoring
    checks that get installed.
    """
    variables = {}
    path = pathlib.Path(pathlib.PurePath(root, vars_dir))

    for var_file in path.glob("*.yml"):
        with var_file.open("r") as f:
            variables.update(yaml.load(f.read()))

    # This is generated during playbook runtime via a `set_fact`
    # so fake this out here.
    variables["maas_swift_access_url_key"] = "maas_swift_access_url_key"

    return variables


def _get_globals(config_variables):
    """Return a dictionary of globals for the Jinja Environment"""
    # Put enough commonly used variables in here so templates can partially
    # render, but not enough that check-specific variables would cause
    # us to not be able to find the variables involved in an alarm's criteria.
    # This should ideally be, as the name states, variables that are global
    # and apply to most or all checks. They're generally things set in the
    # top-level of each check, like labels.
    global_names = ("inventory_hostname", "ansible_hostname",
                    "ansible_host", "ansible_nodename", "ansible_fqdn",
                    "container_name", "maas_plugin_dir",
                    "maas_lb_name")

    # For most names, just set the value to itself. It's mostly a placeholder.
    new_globals = {k: "<%s>" % k for k in global_names}

    # These regexes get created as a part of a task when the maas playbooks
    # are run.
    new_globals["maas_excluded_checks_regex"] = ""
    new_globals["maas_excluded_alarms_regex"] = ""
    # This is needed for the disk_utilisation check, which iterates over
    # devices. IRL, this list is generated by ansible listing actual
    # devices, so give it a fake list to be happy.
    new_globals["maas_disk_util_devices"] = ["device"]
    # This is needed for the ceph_osd_stats check, which iterates over
    # host IDs. Give it a fake list to be happy.
    new_globals["ceph_osd_host"] = {'osd_ids': ["id"]}

    # The following names are needed during partial template rendering
    # so we can at least create the proper alarms per check, since the
    # checks these names are from create alarms iteratively based on the
    # configured list.
    # NOTE: Don't copy config_variables into new_globals wholesale as we
    # want things such as alarm criteria to remain as actual template values.
    for name in ("elasticsearch_process_names",
                 "ceph_radosgw_protocol",
                 "rsyslogd_process_names",
                 "maas_swift_account_process_names",
                 "maas_swift_container_process_names",
                 "maas_swift_object_process_names",
                 "maas_managed_k8s_auth_process_name",
                 "maas_managed_k8s_etp_process_name",
                 "maas_managed_k8s_etg_process_name",
                 "maas_managed_k8s_ui_process_name"):
        new_globals[name] = config_variables[name]

    # There are a few labels that use `item` from with_items
    # or with_together, so fake them out.
    new_globals["item"] = {"label": "label", "key": "key",
                           "filesystem": "<filesystem>",
                           "clusters": {"name": "<cluster-name>"}}

    # rally_check.yaml.j2 and maas-rally.yml are much more involved than
    # most other checks, in that there's a set of defaults and then
    # each service gets its own application of that template with some
    # service specific values.
    # TODO(briancurtin): consider just not including this in the default
    # and processing rally_check with its own environment separate from
    # everything else. This could end up adversely affecting other checks
    # if they do some mass iteration thing like this does.
    new_globals["item"]["value"] = {}
    prefix = "maas_rally_default_"
    pos = len(prefix)
    rally_keys = (k for k in config_variables if k.startswith(prefix))
    for key in rally_keys:
        new_globals["item"]["value"][key[pos:]] = config_variables[key]

    return new_globals


def _get_check_details(rendered_yaml, config_variables, environment):
    """Return a dictionary of undeclared variables per alarm

    The keys are alarm names, and the value of each alarm is
    a dict of the available values to configure and their
    default value"""
    ignore = (# Ignore maas_alarm_local_consecutive_count because it's not
              # something that should generally be changed, especially
              # because it has an effect on SLAs.
              "maas_alarm_local_consecutive_count",
              "volume_group",
              "console_service_name")

    # The filesystem checks are created in a loop based on what devices
    # are on the target machine, so since we're faking this out and not
    # rendering the template for any specific filesystem device, just look
    # for these names and swap them with what actually gets configured.
    redirect = {"warning_threshold": "maas_filesystem_warning_threshold",
                "critical_threshold": "maas_filesystem_critical_threshold"}

    # Look for undeclared variables within the top-level `alarms`
    alarms = rendered_yaml.get("alarms") or {}
    # Skip to taking only the key and critera of each alarm. Ignore the rest.
    alarms = {key: value["criteria"] for key, value in alarms.items()}

    # Look for undeclared variables within the top-level `details`
    check_details = rendered_yaml.get("details") or {}
    # The args here are lower level than we want to be documenting.
    # They're also problematic in that it means we have to fake out
    # a lot more lower level Ansible-specific names, like fake inventory.
    if "args" in check_details:
        check_details.pop("args")

    details = {}
    for key, value in itertools.chain(alarms.items(), check_details.items()):
        # Skip the file and url settings from details. Those are compound
        # settings and not really something to be changing.
        if key in ("file", "url"):
            continue

        ast = environment.parse(value)
        undeclared = jinja2.meta.find_undeclared_variables(ast)

        for item in ignore:
            if item in undeclared:
                undeclared.remove(item)

        # If we have variables which are effectively controlled by
        # other variables, swap them out with the root variable
        # that should be modified.
        for redirect_key, redirect_value in redirect.items():
            if redirect_key in undeclared:
                undeclared.remove(redirect_key)
                undeclared.add(redirect[redirect_key])

                # Include this change in the actual config_variables
                # so the critera gets rendered properly.
                config_variables[redirect_key] = config_variables[
                    redirect_value]

        # Fill in the undeclared variables with their actual default
        # from the maas yaml configs.
        defaults = {key: config_variables[key] for key in undeclared}

        # These details are check-wide. Without this sort of key,
        # we end up having a lot more top-level keys in the details
        # dict than we'll want, with names that won't mean much.
        if key in check_details:
            key = "_check_variables"

            if not defaults:
                continue

        if key in details:
            details[key].update(defaults)
        else:
            details[key] = defaults

        # If this is an alarm, value will be the "criteria" DSL content.
        # Render it with the default variables and store it so the DSL
        # transform can use it.
        if key in alarms.keys():
            criteria_template = jinja2.Template(value)
            rendered_criteria = criteria_template.render(config_variables)
            details[key]["_criteria"] = _get_criteria(rendered_criteria)

    return details


def _get_criteria(criteria):
    """Yield dictionaries with status, message, and condition"""
    # Since we get multiple conditions sent in criteria, look at them
    # one at a time and group them together.
    lines = criteria.split("\n")

    status_names = ("CRITICAL", "WARNING", "OK")

    # We match on status but look back for its condition.
    condition = None

    all_criteria = []

    for line in lines:
        match = CRITERIA.search(line)
        if match:
            # The regex matches *with* the outer parens. Strip them off.
            # TODO(briancurtin): Figure out a regex that leave parens off.
            content = match.group(0)[1:-1]
            if any([content.startswith(status) for status in status_names]):
                # A fall-through return status won't be paired with any
                # condition so rename it for display purposes.
                if condition is None:
                    condition = "default"

                comma = content.find(",")
                status = content[:comma]

                # Anything after the comma is our message content
                message = content[comma + 1:]
                message = message.strip()
                # Trim the outer strings
                message = message[1:-1]

                all_criteria.append({"status": status, "message": message,
                                     "condition": condition})
                condition = None
            else:
                condition = content

    return all_criteria


def _lookup(*args, **kwargs):
    """
    Rather than write an actual ansible lookup plugin, just give the
    config name back if we can.
    """
    if args:
        if args[0] == "pipe":
            return "ignore"
        if args[0] == "env":
            return args[1]
    return "ignore"


def _ipaddr(*args, **kwargs):
    """Fake ipaddr filter"""
    return "ipaddr"


def check_details(root, templates_dir=TEMPLATES_DIR):
    """Yield check names and a generator of their details.

    This yields a tuple, where the first value is the check label,
    the second is the category, and the third is a dictionary of
    details about the alarms within that check.

    The keys of the dictionary are alarm names plus the special key
    "_check_variables" which are not specific to any one alarm.
    The _check_variables value is a dictionary of configurable
    names and their default values.

    The values for any of the alarm names include any of the
    configurable values used by the alarm along with their defaults,
    as well as a special key "_criteria", which is a list of
    dictionaries representing status/condition/message for situations
    which trigger the alarm.

    Example return value:

    ("private_ping_check--inventory_hostname",
     "host",
     {'_check_variables': {'private_ping_check_count': 6},
      'Packet_loss': {
        '_criteria': [{'condition': "metric['available'] > 80",
                       'status': "OK", 'message': 'Ping responds as expected'},
                      {'condition': 'default',
                       'status': 'CRITICAL',
                       'message': 'Packet loss has occurred'}]}})
    """
    config_variables = _get_defaults(root)

    rax_maas_path = pathlib.Path(pathlib.PurePath(root, templates_dir))
    # Some templates inside rax_maas_path refer to
    # "templates/common/macros.jinja", so we need to make one level above
    # that available to the FileSystemLoader. That's `playbooks/`
    playbooks_root = pathlib.Path(pathlib.PurePath(root, PLAYBOOKS_DIR))

    # The things we care about and are going to iterate over later on
    # come from rax_maas_path, so make playbooks_root the fallback.
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([str(rax_maas_path),
                                        str(playbooks_root)]),
        undefined=SilentUndefined)
    env.globals = _get_globals(config_variables)
    env.globals.update(lookup=_lookup)

    # Since we're looking specifically at Ansible templates, we need to bring
    # a few things into the standard Jinja2 filters that we end up using.
    env.filters.update(ansible_filters.FilterModule().filters())
    env.filters.update(ansible_tests.TestModule().tests())
    env.filters.update(ipaddr=_ipaddr)

    for template_file in rax_maas_path.glob("*.yaml.j2"):
        # Skip some templates we're not meant to expose
        if template_file.name in IGNORED_TEMPLATES:
            continue

        template = env.get_template(str(template_file.name))

        # Render the check template but don't pass it any variables.
        # It'll be partially rendered as it's going to have some globals
        # filled in.
        # TODO(briancurtin): When new checks are added and we don't properly
        # handle any new variables they've added, this is where it blows up.
        # For example, all of the variables we fake out in _get_globals
        # are there because they cause an issue at this point. It would be
        # ideal for us to be able to output at this point that something
        # is blocking the render here and allow us to continue with the
        # rest of the checks, but we are currently unable to catch an
        # exception here because it is apparently raised from within
        # the jinja2.Environment. Ideally we're able to capture that
        # exception and probably pass it to some type of handler that the
        # caller gives so that documentation isn't entirely killed.
        partially_rendered_template = template.render()

        # Load this with the RemappingLoader so we can catch things like
        # {{ private_ssh_port }}, which isn't wrapped in quotes,
        # and is thus unhashable as a mapping key within pyyaml.
        rendered_yaml = yaml.load(partially_rendered_template,
                                  Loader=RemappingLoader)

        # TODO(briancurtin): The network_throughput related variables
        # aren't included here as that check loops over other variables
        # that aren't yet covered.
        details = _get_check_details(rendered_yaml, config_variables, env)

        try:
            category = rendered_yaml["metadata"]["rpc_check_category"]
        except KeyError:
            # This will only fall through if the get_metadata macro
            # wasn't included on the check template.
            # If included like it's supposed to be, that macro
            # will always return some category.
            category = "uncategorized"

        try:
            label = template.module.label
        except AttributeError:
            label = rendered_yaml.get("label")

        yield (label, category, details)


def categorized_check_details(root, templates_dir=TEMPLATES_DIR):
    """Return categories and their corresponding checks

    This returns a dict where the keys are categories and the values
    are themselves a dictionary of checks in that category.

    The checks dictionary has keys representing a check's name, and then
    the values are a dictionary of details about the alarms within
    that check.

    The keys of the alarms dictionary are alarm names plus the special
    key "_check_variables" which are not specific to any one alarm.
    The _check_variables value is a dictionary of configurable
    names and their default values.

    The values for any of the alarm names include any of the
    configurable values used by the alarm along with their defaults,
    as well as a special key "_criteria", which is a list of
    dictionaries representing status/condition/message for situations
    which trigger the alarm.

    Example return value:

    {'host': {
        "private_ping_check--<inventory_hostname>": {
            '_check_variables': {'private_ping_check_count': 6},
            'Packet_loss': {
                '_criteria': [
                    {'condition': "metric['available'] > 80",
                     'status': "OK", 'message': 'Ping responds as expected'},
                    {'condition': 'default',
                     'status': 'CRITICAL',
                     'message': 'Packet loss has occurred'}]
            }
        }
    }
    """
    categorized = collections.defaultdict(dict)
    for check, category, details in list(check_details(root)):
        categorized[category][check] = details

    return categorized


def _main():
    for category, checks in categorized_check_details("../../..").items():
        print("Category: {}".format(category))
        for check, details in checks.items():
            print("\tCheck: {}".format(check))
            for alarm, variables in details.items():
                print("\t\tAlarm: {}".format(alarm))
                for key, value in variables.items():
                    if key == "_criteria":
                        for criteria in value:
                            for typ, parameter in criteria.items():
                                print("\t\t\t{}: {}".format(typ, parameter))
                    else:
                        print("\t\t\tVariable: {} = {}".format(key, value))



if __name__ == "__main__":
    _main()
