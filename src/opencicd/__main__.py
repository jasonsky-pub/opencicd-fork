#
#              Copyright 2025 Comcast Cable Communications Management, LLC
#
#              Licensed under the Apache License, Version 2.0 (the "License");
#              you may not use this file except in compliance with the License.
#              You may obtain a copy of the License at
#
#              http://www.apache.org/licenses/LICENSE-2.0
#
#              Unless required by applicable law or agreed to in writing, software
#              distributed under the License is distributed on an "AS IS" BASIS,
#              WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#              See the License for the specific language governing permissions and
#              limitations under the License.
#
#              SPDX-License-Identifier: Apache-2.0
#
#              This product includes software developed at Comcast (https://www.comcast.com/).#
import argparse
import asyncio
import json
import logging
import os
import platform
import sys

from typing import Optional

from opencicd import constants
from opencicd import __semver__ as module_semver
from opencicd import __version__ as module_version
from opencicd.action_runner import run_action, RunMethod
from opencicd.model.action import Action, load_action
from opencicd.model.project import Project
from opencicd.model.serialization import deserialize_enum
from opencicd.output import OutputFormat, output_list


async def async_main(args):
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--debug", required=False,
                            help="Debug mode is enabled or not", action=argparse.BooleanOptionalAction)

    arg_parser.add_argument("--version", required=False,
                            help="Print version and exit", action=argparse.BooleanOptionalAction)

    arg_parser.add_argument("--project-folder", required=False, help="Specify Root Project Folder accessible by this process: (default .)")
    arg_parser.add_argument("--host-project-folder", required=False, help="Specify Root Project Folder on the host: (default .), can be different from project-folder in the case of method=print")
    arg_parser.add_argument("--container-project-folder", required=False, help="Specify Root Project Folder inside the container (default /work)")
    arg_parser.add_argument("--docker-user", required=False, help="Specify the docker runtime user value to pass to docker run --user")
    arg_parser.add_argument("--tmp-home", required=False,
                            help="Add a tmpfs-backed HOME directory for runtime docker run commands", action=argparse.BooleanOptionalAction)

    arg_parser.add_argument("-o", "--output-format", required=False,
                            help="output format to use, \"raw\", \"json\", \"yaml\"")

    arg_parser.add_argument("--input-env", required=False, help="Environment variable which is an input, can supply many, ex: --input-env VAR_NAME", action='append')
    arg_parser.add_argument("--input-json", required=False, help="JSON Dictionary of Inputs, can supply many", action='append')
    arg_parser.add_argument("--input-json-env", required=False, help="Environment variable which includes a JSON Dictionary of inputs to pass, can supply many, ex: --input-json-env VAR_NAME", action='append')
    arg_parser.add_argument("--input-remove", required=False, help="The name of an input to REMOVE and not pass, runs after other input commands, can supply many, ex: --input-remove myInputName", action='append')
    arg_parser.add_argument("--secret-env", required=False, help="Environment variable which is a secret, can supply many, ex: --secret-env VAR_NAME", action='append')
    arg_parser.add_argument("--secret-json", required=False, help="JSON Dictionary of Secrets, can supply many", action='append')
    arg_parser.add_argument("--secret-json-env", required=False, help="Environment variable which includes a JSON Dictionary of secrets to pass, can supply many, ex: --secret-json-env VAR_NAME", action='append')
    arg_parser.add_argument("--secret-remove", required=False, help="The name of a secret to REMOVE and not pass, runs after other input commands, can supply many, ex: --secret-remove mySecretName", action='append')
    arg_parser.add_argument("--input", required=False, help="Input value to pass, can supply many, ex: --input name=value", action='append')
    arg_parser.add_argument("--secret", required=False, help="Secret value to pass, can supply many, ex: --secret name=value", action='append')

    arg_parser.add_argument("--cicd", required=False, default=False,
        help="Assume environment variables prefixed with INPUT_, INPUTJSON_ are inputs and SECRET_, SECRETJSON_ are secrets. ex: INPUT_PARAM=123 -> PARAM=123, INPUTJSON_VARS=\"{...}\" assigns it's entries",
        action=argparse.BooleanOptionalAction)

    arg_parser.add_argument("--quiet", required=False, default=False,
                            help="Do not print messages for each job/action run", action=argparse.BooleanOptionalAction)

    arg_parser.add_argument("--list-action-types", required=False,
                            help="List the action types available on this project", action=argparse.BooleanOptionalAction)
    arg_parser.add_argument("--list-actions", required=False, help="List actions for an action type",
                  action=argparse.BooleanOptionalAction)

    arg_parser.add_argument("--method", required=False,
                            help="Run-method, \"print\" to print commands to screen, \"exec\" to execute commands directly (default exec)")
    arg_parser.add_argument("--posix", required=False, action=argparse.BooleanOptionalAction,
                            help="to use posix commands (*nix) to remove temporary resources and handle error conditions.  Only applies to method=print")

    arg_parser.add_argument('action_type', help='Which action type to process', nargs='?', default="")
    arg_parser.add_argument('action', help='Which action', nargs='?', default="")

    if len(args) == 1:
        arg_parser.print_help()
        exit(-1)

    result = arg_parser.parse_args(args[1:])
    cicd_debug = os.environ.get('DEBUG') or "False"
    if result.debug or (result.cicd and cicd_debug.lower() == "true"):
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    quiet = result.quiet

    logging.debug(f"Python version: {platform.python_version()}")

    method = RunMethod.Exec
    if result.cicd:
        method = RunMethod.Print

    if result.method:
        method = deserialize_enum(result.method, RunMethod)

    if result.version or not quiet:
        if method == RunMethod.Print:
            print(f"echo opencicd v{module_semver}")
        elif module_semver == module_version:
            print(f"opencicd v{module_semver}")
        else:
            print(f"opencicd v{module_semver} (PyPI {module_version})")

    if result.version:
        exit(0)

    project_folder = None
    host_project_folder = None
    container_project_folder = None

    if result.cicd:
        project_folder = os.environ.get("PROJECT_FOLDER")
        host_project_folder = os.environ.get("HOST_PROJECT_FOLDER")
        container_project_folder = os.environ.get("CONTAINER_PROJECT_FOLDER")

    if result.project_folder:
        project_folder = result.project_folder

    if result.host_project_folder:
        host_project_folder = result.host_project_folder

    if result.container_project_folder:
        container_project_folder = result.container_project_folder

    if project_folder is None:
        project_folder = os.curdir

    if host_project_folder is None:
        host_project_folder = os.curdir

    if container_project_folder is None:
        container_project_folder = constants.default_container_project_folder

    docker_user = result.docker_user
    tmp_home = result.tmp_home
    if tmp_home is None:
        tmp_home = result.cicd

    logging.debug(f"Project folder: {project_folder}")
    logging.debug(f"Host Project folder: {host_project_folder}")
    logging.debug(f"Container Project folder: {container_project_folder}")

    output_format = OutputFormat.raw
    if result.output_format:
        output_format = deserialize_enum(result.output_format, OutputFormat)

    project = Project(project_folder, host_project_folder, container_project_folder)
    if result.list_action_types:
        actions = project.get_actions()
        actionlist = [x for x in actions.keys()]
        output_list(actionlist, output_format)
        return

    action_type_name = None
    action_name = None

    if result.cicd:
        action_type_name = os.environ.get("ACTION_TYPE")
        action_name = os.environ.get("ACTION")

    if result.action_type:
        action_type_name = result.action_type

    if result.action:
        action_name = result.action

    if result.list_actions:
        if action_type_name is None or action_type_name == "":
            raise ValueError("action_type is required if --list-actions is specified")

        actions = project.get_actions()

        project_actions = actions.get(action_type_name) or []

        action_names = [project_action.name for project_action in project_actions]
        output_list(action_names, output_format)
        return

    # Add INPUTJSON_ into inputs
    inputs = {}
    input_json_dictionaries = result.input_json or []

    if result.cicd:
        add_environment_into_dictionary("Input", True, "INPUT_", inputs)
        add_environment_into_list("Input", True, "INPUTJSON_", input_json_dictionaries)

    collect_mappings(
        "Input",
        True,
        result.input,
        result.input_env,
        input_json_dictionaries,
        result.input_json_env,
        result.input_remove,
        inputs
    )

    secrets = {}
    secret_json_dictionaries = result.secret_json or []

    if result.cicd:
        add_environment_into_dictionary("Secret", False, "SECRET_", secrets)
        add_environment_into_list("Secret", False, "SECRETJSON_", secret_json_dictionaries)

    collect_mappings(
        "Secret",
        False,
        result.secret,
        result.secret_env,
        secret_json_dictionaries,
        result.secret_json_env,
        result.secret_remove,
        secrets
    )

    use_posix = True

    if result.posix is not None:
        use_posix = result.posix

    if action_type_name is None or action_type_name == "":
        raise ValueError("Please specify action_type")

    if method == RunMethod.Print and use_posix:
        print("set -e")

    if action_name is None or action_name == "":
        actions = project.get_actions()

        project_actions = actions.get(action_type_name)
        if project_actions is None:
            logging.warning("Action Type not found: " + action_type_name)
            return

        actions = [load_action(x) for x in project_actions]
        ordered_actions = action_organizer(actions)
        for action in ordered_actions:
            run_action(project, action, method, inputs, secrets, use_posix, quiet, docker_user, tmp_home)
        return

    actions = project.get_actions()

    project_actions = actions.get(action_type_name)
    if project_actions is None:
        raise RuntimeError("Action Type not found: " + action_type_name)

    project_action = next(
        (
            project_action for project_action in project_actions if project_action.name == action_name
        ),
        None
    )

    if project_action is None:
        raise RuntimeError("Action not found: " + action_name)

    action = load_action(project_action)

    run_action(project, action, method, inputs, secrets, use_posix, quiet, docker_user, tmp_home)


def main():
    asyncio.run(async_main(sys.argv))

def action_organizer(actions: list[Action]) -> list[Action]:
    remaining_actions = actions.copy()
    resulting_actions = []

    while remaining_actions:
        found_any = False
        for action in remaining_actions:
            dependencies_clear = True

            if action.dependencies is not None:
                for dependency in action.dependencies:
                    if dependency not in [x.project_action.name for x in resulting_actions]:
                        dependencies_clear = False

            if dependencies_clear:
                found_any = True
                resulting_actions.append(action)
                remaining_actions.remove(action)
                break

        if not found_any:
            current_order = "".join([x.project_action.name for x in resulting_actions])
            remaining_actions = "".join([x.project_action.name for x in remaining_actions])
            raise RuntimeError(f"Missing or circular dependency detected in actions.  Dependencies Resolved: {current_order} / Dependencies not resolved: {remaining_actions}")

    return resulting_actions



def collect_mappings(
    type_description: str,
    debug_values: bool,
    key_value_strings: Optional[list[str]],
    env_names: Optional[list[str]],
    json_dictionaries: Optional[list[str]],
    env_json_names: Optional[list[str]],
    remove_keys: Optional[list[str]],
    into_dictionary: dict[str, str]
):

    if key_value_strings:
        for key_value in key_value_strings:
            parts = key_value.split("=", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid {type_description}: \"{key_value}\", format expected 'key=value'")
            key = parts[0]
            value = parts[1]
            into_dictionary[key] = value

    if env_names:
        for var_name in env_names:
            value = os.environ.get(var_name)
            if value is None or value.strip() == "":
                logging.warning(f"Expected Environment Variable for {type_description} not present or has no value: {var_name}")
                continue

            if value is not None:
                into_dictionary[var_name] = value

    json_documents = []

    if json_dictionaries:
        for doc in json_dictionaries:
            json_documents.append(doc)

    if env_json_names:
        for var_name in env_json_names:
            value = os.environ.get(var_name)
            if value is None or value.strip() == "":
                logging.warning(f"Expected Environment Variable for {type_description} not present or has no value: {var_name}")
                continue
            json_documents.append(value)

    for data_json in json_documents:
        json_dictionary = json.loads(data_json)
        for key in json_dictionary.keys():
            if not isinstance(key, str):
                raise TypeError(f"key in {type_description} is not a string")
            value = json_dictionary[key]
            if not isinstance(value, str):
                value = value.__str__()
            into_dictionary[key] = value

    if remove_keys:
        for remove_key in remove_keys:
            existing = into_dictionary.get(remove_key)
            if existing:
                logging.debug(f"Removing {type_description}: {remove_key}")
                into_dictionary.pop(remove_key)

    if into_dictionary:
        logging.debug(f"Mappings found [{type_description}]:")
        for (key, value) in into_dictionary.items():
            logging.debug(f"\t{key}{(('=' + value) if debug_values else '')}")
    else:
        logging.debug(f"Mappings empty [{type_description}]")


def add_environment_into_dictionary(
    type_description: str,
    debug_values: bool,
    prefix: str,
    into_dictionary: dict[str, str]
):
    for (key, value) in os.environ.items():
        if key.lower().startswith(prefix.lower()) and value is not None and value.strip() != "":
            non_prefix_key = key[len(prefix):]
            logging.debug(f"Found {type_description} environment variable: {key} -> {non_prefix_key}{('=' + value) if debug_values else ''}")
            into_dictionary[non_prefix_key] = value

def add_environment_into_list(
    type_description: str,
    debug_values: bool,
    prefix: str,
    into_list: list[str]
):
    for (key, value) in os.environ.items():
        if key.lower().startswith(prefix.lower()) and value is not None and value.strip() != "":
            logging.debug(f"Found {type_description} environment variable: {key}{(' -> ' + value) if debug_values else ''}")
            into_list.append(value)

if __name__ == '__main__':
    main()
