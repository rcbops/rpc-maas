#!/usr/bin/env python
# Copyright 2019, Rackspace US, Inc.
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

import logging
import os
import shutil

import maas_checks_config

PREFIX = "MAAS_CHECKS_PLUGIN:"
CHECKOUT_ROOT = "../../.."


def _get_details(file_name, app):
    """Yield the details of this file name

    When no content is found or the file does not exist, yield the
    empty string so it results in no effect to the rendered output.
    """
    if os.path.exists(file_name):
        content = open(file_name, "r").read()
        if content:
            yield content
        else:
            yield ""
            # TODO(briancurtin): We may want to move this to be a warn instead
            # if an info in the future, at least after the initial content
            # is provided. If we do that, then 100% of things will require
            # an explanation (which I think we should do).
            app.info("{prefix} No content in {file_name}".format(
                     prefix=PREFIX, file_name=file_name))
    else:
        yield ""
        app.warn("{prefix} Did not find {file_name}".format(
                 prefix=PREFIX, file_name=file_name))


def _mkdir_p(path):
    """Python implementation of `mkdir -p <path>`
    :param path: ``str``
    """
    try:
        if not os.path.isdir(path):
            os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise OSError(
                'The provided path can not be created into a directory.'
            )


def _make_file(file_name):
    if not os.path.exists(file_name):
        _mkdir_p(path=os.path.dirname(file_name))
        with open(file_name, 'w') as f:
            f.write('')


def get_category_details(category, app):
    file_name = os.path.join(app.srcdir, "stubs", category, "title.rst")
    _make_file(file_name)
    yield from _get_details(file_name, app)


def get_check_details(category, check, app):
    file_name = os.path.join(app.srcdir, "stubs", category, check, "title.rst")
    _make_file(file_name)
    yield from _get_details(file_name, app)


def get_alarm_details(category, check, alarm, app):
    file_name = os.path.join(app.srcdir, "stubs", category, check,
                             "{alarm}.rst".format(alarm=alarm))
    _make_file(file_name)
    yield from _get_details(file_name, app)


def render_all_details(check_details, app):
    # Alpha sort these so we don't generate randomly ordered pages.
    categories = sorted(check_details.keys())

    for category in categories:
        yield from render_category(category, check_details, app)


def render_category(category, check_details, app):
    category_label = "**{category}**".format(category=category)
    yield "\n{category_label}\n".format(category_label=category_label)
    yield "*" * len(category_label)
    yield "\n"

    yield from get_category_details(category, app)

    for check, details in check_details[category].items():
        yield "\n{check}\n".format(check=check)
        yield "=" * len(check)
        yield "\n"

        yield from get_check_details(category, check, app)

        check_variables = None
        if "_check_variables" in details:
            check_variables = details.pop("_check_variables")
            #if not cv:
            #    continue
            s = "s" if len(check_variables) > 1 else ""

            yield "\n* Check-wide variable{s} ::\n\n".format(s=s)
            for check_variable, check_default in check_variables.items():
                yield "\t{variable} = {default}\n".format(
                    variable=check_variable, default=check_default)

        for alarm_name, alarm_details in details.items():
            alarm_title = "Alarm: {alarm_name}".format(
                alarm_name=alarm_name)
            yield "\n{alarm_title}\n".format(alarm_title=alarm_title)
            yield "-" * len(alarm_title)
            yield "\n"

            yield from get_alarm_details(category, check, alarm_name, app)

            if "_criteria" in alarm_details:
                criteria = alarm_details.pop("_criteria")

            num_details = len(alarm_details)
            if num_details > 0:
                plural = "s" if num_details > 1 else ""

                yield "\n* Variable{plural} ::\n\n".format(plural=plural)
                for variable, value in alarm_details.items():
                    yield "\t{variable} = {value}\n".format(variable=variable,
                                                            value=value)

            status_len = 10
            condition_len = 250
            message_len = 250

            def new_line(char):
                yield "".join(["+", char * status_len,
                               "+", char * condition_len,
                               "+", char * message_len, "+\n"])

            def content(block):
                yield "".join(
                    ["|" + block["status"].ljust(status_len, " ") +
                     "|" + block["condition"].ljust(condition_len, " ") +
                     "|" + block["message"].ljust(message_len, " ") +
                     "|\n"])

            yield "\n"

            # Top line
            for dash in new_line("-"):
                yield dash
            yield ("|" + "Status".ljust(status_len, " ") +
                   "|" + "Condition".ljust(condition_len, " ") +
                   "|" + "Message".ljust(message_len, " ") + "|\n")
            # Header separator
            for equals in new_line("="):
                yield equals

            for block in criteria:
                for item in content(block):
                    yield item
                for dash in new_line("-"):
                    yield dash

            # Put the criteria back in for further iterations.
            alarm_details["_criteria"] = criteria

        if check_variables is not None:
            # Put the check variables back in for further iterations.
            details["_check_variables"] = check_variables


def cleanup_path(app, path):
    if os.path.exists(path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            app.info("{prefix} Removed {path}".format(prefix=PREFIX,
                                                      path=path))
        except OSError:
            app.warn("{prefix} Unable to remove {path}".format(prefix=PREFIX,
                                                               path=path))


def builder_inited(app):
    # NOTE: This is executed from the top-level of the checkout, so using
    # the current working directory is already properly set.
    check_details = maas_checks_config.categorized_check_details(os.getcwd())

    single_page = "".join(render_all_details(check_details, app))
    with open("{root}/all_checks.rst".format(root=app.srcdir), "w") as f:
        f.write(":orphan:\n\n")
        f.write("================================\n")
        f.write("All monitoring checks and alarms\n")
        f.write("================================\n\n")
        f.write(".. contents:: Categories\n")
        f.write("\t:depth: 1\n")
        f.write("\t:local:\n\n")
        f.write(single_page)

    categories = list(check_details.keys())

    cat_dir = "{root}/categories".format(root=app.srcdir)
    # This shouldn't exist, but remove it in case it got left behind.
    cleanup_path(app, cat_dir)
    os.mkdir(cat_dir)

    for category in categories:
        # name and path are different, as name is a reference within
        # the Sphinx environment (relative to app.srcdir) and the path
        # is a full file path.
        page_name = "categories/{category}".format(category=category)
        page_path = "{root}/{category}.rst".format(root=cat_dir,
                                                   category=category)
        with open(page_path, "w") as f:
            f.write("".join(render_category(category, check_details, app)))


def build_finished(app, exception):
    cleanup_path(app, "{root}/categories".format(root=app.srcdir))
    cleanup_path(app, "{root}/all_checks.rst".format(root=app.srcdir))


def setup(app):
    app.connect("builder-inited", builder_inited)
    app.connect("build-finished", build_finished)

