#
#             Copyright 2025 Comcast Cable Communications Management, LLC
#             Licensed under the Apache License, Version 2.0 (the "License");
#             you may not use this file except in compliance with the License.
#             You may obtain a copy of the License at
#
#             http://www.apache.org/licenses/LICENSE-2.0
#
#             Unless required by applicable law or agreed to in writing, software
#             distributed under the License is distributed on an "AS IS" BASIS,
#             WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#             See the License for the specific language governing permissions and
#             limitations under the License.
#
#             SPDX-License-Identifier: Apache-2.0
#
import logging
import os.path
import random
import re
import string
import subprocess
from enum import Enum

from opencicd import constants
from opencicd.model.action import Action, load_action
from opencicd.model.job import Job, EntrypointType
from opencicd.model.project import ProjectAction, Project


class RunMethod(Enum):
    Print=1
    Exec=2

def run_action(
    project: Project,
    action: Action,
    run_method: RunMethod,
    inputs: dict[str, str],
    secrets: dict[str, str],
    use_posix: bool,
    quiet: bool
):
    project_action = action.project_action
    if not quiet:
        display_text(
            run_method,
            quiet,
            f"Processing action-type[{project_action.action_type}], action[{project_action.name}]",
            use_posix
        )
    action.validate()
    job_number=1
    for job in action.jobs:
        job_runner(project, project_action, action, job, run_method, inputs, secrets, use_posix, quiet, job_number)
        job_number=job_number+1

def display_text(
    run_method: RunMethod,
    quiet: bool,
    text: str,
    use_posix: bool
):
    if not quiet:
        if run_method == RunMethod.Exec:
            print(text, flush=True)
        else:
            if use_posix:
                print("echo \"" + safe_quote(text) + "\"", flush=True)
            else:
                # Fallback to logging when can't use posix
                logging.warn(text)

def job_runner(
    project: Project,
    project_action: ProjectAction,
    action: Action,
    job: Job,
    run_method: RunMethod,
    inputs: dict[str, str],
    secrets: dict[str, str],
    use_posix: bool,
    quiet: bool,
    job_number: int
):
    display_text(
        run_method,
        quiet,
        f"Processing action-type[{project_action.action_type}], action[{project_action.name}], job[{job_number}]",
        use_posix
    )

    replacement_values = build_replacement_values(
        project,
        project_action,
        action,
        job,
        inputs,
        secrets
    )

    command_array = [
        text("docker"),
        text("run"),
        text("--rm"),
        text("--workdir"),
        text(project.container_project_folder),
        text("--volume"),
        text(f"{project.host_project_folder}:{project.container_project_folder}")
    ]

    if job.volumes:
        for key, value in job.volumes.items():
            volume_source = replace_values(key, replacement_values)
            volume_destination = replace_values(value, replacement_values)
            command_array.append(text("--volume"))
            command_array.append(volume_source.append(text(":")).append(volume_destination))

    # Add environment variables:
    for (key, value) in replacement_values.items():
        command_array.append(text(f"-e"))
        command_array.append(text(f"{key}=").append(value))

    # prepare arguments:
    args: list[SecretableText] = []
    if job.arguments:
        for arg in job.arguments:
            args.append(replace_values(arg, replacement_values))


    if job.entrypoint_type == EntrypointType.Override:
        command_array.append(text("--entrypoint"))
        command_array.append(replace_values(job.entrypoint_override, replacement_values))
    elif job.entrypoint_type == EntrypointType.Script:
        command_array.append(text("--entrypoint"))
        command_array.append(text("sh"))

    pre_run_commands = []
    cleanup_image = False
    post_run_commands = []

    if job.login_username:
        pre_run_commands.append(
            [
                text("docker"),
                text("login"),
                text("--username"),
                replace_values(job.login_username, replacement_values),
                text("--password"),
                replace_values(job.login_password, replacement_values),
                replace_values(job.login_registry, replacement_values)
            ]
        )



    if job.image is not None:
        image = replace_values(job.image, replacement_values)
    elif job.dockerfile is not None:
        image = text(generate_random_string(10).lower() + ":latest")
        display_text(
            run_method,
            quiet,
            f"Generating docker image {image.displayable_value} from {job.dockerfile}",
            use_posix
        )
        dockerfile = replace_values(job.dockerfile, replacement_values)
        relative_filename = norm_relative_path(dockerfile)

        docker_build_command = [
            text("docker"),
            text("build"),
            text("-t"),
            image,
            text("-f"),
            relative_filename
        ]

        # Add environment variables:
        for (key, value) in replacement_values.items():
            docker_build_command.append(text(f"--build-arg"))
            docker_build_command.append(text(f"{key}=").append(value))

        if not job.build_context:
            # By default, use the project root folder as the build path:
            build_folder = text(project.host_project_folder)
        else:
            # if the build-context is specified, use that path instead as the "context"
            build_context = replace_values(job.build_context, replacement_values)
            relative_filename = norm_relative_path(build_context)
            build_folder = text(project.host_project_folder).path_join(relative_filename)

        docker_build_command.append(build_folder)

        pre_run_commands.append(
            docker_build_command
        )

        if job.build_output_file:
            replaced_filename = replace_values(job.build_output_file, replacement_values)
            relative_filename = norm_relative_path(replaced_filename)

            output_dir = os.path.dirname(relative_filename.secret_value)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            docker_save_command = [
                text("docker"),
                text("save"),
                text("-o"),
                relative_filename,
                image
            ]
            pre_run_commands.append(
                docker_save_command
            )
        if job.build_output_name_file:
            replaced_filename = replace_values(job.build_output_name_file, replacement_values)
            relative_filename = norm_relative_path(replaced_filename)

            output_dir = os.path.dirname(relative_filename.secret_value)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            if run_method == RunMethod.Exec:
                with open(relative_filename.secret_value, "w") as file: file.write(image.secret_value)
            else:
                if not use_posix:
                    raise RuntimeError("To output a build-output-name-file either run as exec or posix")
                pre_run_commands.append(
                    [
                        text("echo"),
                        image,
                        text(">", dont_quote=True),
                        relative_filename
                    ]
                )

        cleanup_image = True
    elif job.image_file is not None:

        image_file = replace_values(job.image_file, replacement_values)
        image_relative_filename = norm_relative_path(image_file)

        if job.image_name:
            if job.image_name_file:
                raise ValueError("Cannot specify both image-name and image-name-file together")
            image = replace_values(job.image_name, replacement_values)
        else:
            if job.image_name_file:
                image_name_file = replace_values(job.image_name_file, replacement_values)
                name_relative_filename = norm_relative_path(image_name_file)

                if run_method == RunMethod.Exec:
                    with open(name_relative_filename.secret_value, "r") as file:
                        image = text(file.read())
                else:
                    if not use_posix:
                        raise RuntimeError("To output a build-output-name-file either run as exec or posix")
                        # when printing, tag the loaded image at runtime with a known value:
                    image = text("$(cat " + name_relative_filename.secret_value + ")", True)
            else:
                raise ValueError("Must specify either image-name or image-name-file when using image-file")

        pre_run_commands.append(
            [
                text("docker"),
                text("image"),
                text("load"),
                text("-i"),
                image_relative_filename
            ]
        )
        cleanup_image = True

    else:
        raise Exception("No image specified")

    if job.push_image:
        if not job.push_tags:
            raise Exception("No push-tags specified")

        push_image = replace_values(job.push_image, replacement_values)
        image_tags = []
        if job.push_tags:
            push_tags_replaced = replace_values(job.push_tags, replacement_values)
            for image_tag in push_tags_replaced.re_split(r'[,\n\r]'):
                image_tags.append(push_image.append(text(":")).append(image_tag))

        for image_tag in image_tags:
            post_run_commands.append(
                [
                    text("docker"),
                    text("image"),
                    text("tag"),
                    image,
                    image_tag
                ]
            )
            post_run_commands.append(
                [
                    text("docker"),
                    text("image"),
                    text("push"),
                    image_tag
                ]
            )
            post_run_commands.append(
                [
                    text("docker"),
                    text("rmi"),
                    image_tag
                ]
            )

    command_array.append(image)

    if job.entrypoint_type != EntrypointType.Script:
        # Add arguments normally
        for arg in args:
            command_array.append(arg)
    else:
        # Add arguments as arguments for the sh parameter
        arg_smush = smush(args)

        script_path = project.container_project_folder + "/" + job.entrypoint_script
        command_array.append(text("-c"))
        command_array.append(
            text(
                f"chmod +x \"{script_path}\" && \"{script_path}\" "
            ).append(arg_smush)
        )

    cleanup_command = None

    if cleanup_image:
        cleanup_command = [
            text("docker"),
            text("rmi"),
            text("-f"),
            image
        ]

        # only use trap on print since we can manually catch ourselves
        if run_method == RunMethod.Print and use_posix:
            pre_run_commands.append(
                    [
                        text("trap"),
                        join_values(cleanup_command, text(" ")),
                        text("EXIT")
                    ]
                )
            post_run_commands.append(
                [
                    text("trap"),
                    text("-"),
                    text("EXIT")
                ]
            )

        post_run_commands.append(
            cleanup_command
        )

    if job.entrypoint_type == EntrypointType.Noop:
        logging.debug("Skipping Noop Command")
        commands = pre_run_commands + post_run_commands
    else:
        commands = pre_run_commands + [command_array] + post_run_commands


    for command in commands:
        if not command:
            logging.debug("Skipping Empty Command")
            continue

        commands_concatenated = text("")

        for command_item in command:
            if command_item is None:
                continue

            if command_item.dont_quote:
                commands_concatenated = commands_concatenated.append(command_item).append(text(" "))
            else:
                commands_concatenated = commands_concatenated.append(text("\"")) \
                    .append(command_item.safe_quote()).append(text("\" "))

        if run_method == RunMethod.Print:
            logging.debug("Printing command: " + commands_concatenated.displayable_value)
            print(commands_concatenated.secret_value)
        else:
            logging.debug("Running command: " + commands_concatenated.displayable_value)
            try:
                run_command(command, project.host_project_folder)
            except Exception as e:
                if cleanup_command is not None:
                    run_command(cleanup_command, project.host_project_folder)
                raise e



class SecretableText:
    def __init__(
        self,
        displayable_value: str,
        secret_value: str,
        dont_safe_quote: bool = False,
        dont_quote: bool = False
    ):
        if displayable_value is None:
            raise ValueError("displayable value cannot be None")
        if secret_value is None:
            raise ValueError("Secret value cannot be None")
        self.displayable_value = displayable_value
        self.secret_value = secret_value
        self.dont_safe_quote = dont_safe_quote
        self.dont_quote = dont_quote

    def append(self, other):
        return SecretableText(
            self.displayable_value + other.displayable_value,
            self.secret_value + other.secret_value
        )

    def has_secret(self):
        return self.displayable_value != self.secret_value

    def path_join(self, other):
        return SecretableText(
            os.path.join(self.displayable_value,other.displayable_value),
            os.path.join(self.secret_value, other.secret_value)
        )

    def re_split(self, regex: str):
        return_list = []

        if self.has_secret():
            for item in re.split(regex, self.secret_value):
                if item.strip():
                    return_list.append(secret(item.strip()))
        else:
            for item in re.split(regex, self.displayable_value):
                if item.strip():
                    return_list.append(text(item.strip()))

        return return_list

    def safe_quote(self):
        if self.dont_safe_quote:
            return self

        return SecretableText(
            safe_quote(self.displayable_value),
            safe_quote(self.secret_value)
        )

def text(value: str, dont_safe_quote: bool = False, dont_quote: bool = False) -> SecretableText:
    return SecretableText(value, value, dont_safe_quote=dont_safe_quote, dont_quote=dont_quote)

def secret(value: str, dont_safe_quote: bool = False) -> SecretableText:
    return SecretableText(constants.secret_replacement_text, value, dont_safe_quote)

def join_values(items: list[SecretableText], delimiter: SecretableText):
    displayable_result = ""
    secret_result = ""
    first = True
    dont_safe_quote = False
    for item in items:
        if not first:
            displayable_result = displayable_result + delimiter.displayable_value
            secret_result = secret_result + delimiter.secret_value
        first = False

        if item.dont_safe_quote:
            dont_safe_quote = True

        displayable_result = displayable_result + item.displayable_value
        secret_result = secret_result + item.secret_value

    return SecretableText(displayable_result, secret_result, dont_safe_quote)



def smush(values: list[SecretableText]) -> SecretableText:
    display_list = ["\"" + safe_quote(arg.displayable_value) + "\"" for arg in values]
    secret_list = ["\"" + safe_quote(arg.displayable_value) + "\"" for arg in values]
    return SecretableText("".join(display_list), "".join(secret_list))


def safe_quote(val: str):
    return val.replace("$", "\\$").replace("\"", "\\\"")


def run_command(
    command: list[SecretableText],
    working_directory: str
):
    # Method = exec:
    secret_command_strings = [cmd.secret_value for cmd in command]
    displayable_command_string = " ".join([cmd.displayable_value for cmd in command])
    try:
        run_result = subprocess.run(
            secret_command_strings,
            cwd=working_directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8'
        )

        outputText = run_result.stdout

    except Exception as e:
        logging.error(f"Error starting sub-process: {displayable_command_string}, error: {e.__str__()}")
        raise e


    if run_result.returncode != 0:
        logging.error(
            "Error in sub-process.  exitCode:" + run_result.returncode.__str__() + ", text: " + outputText)
        raise ChildProcessError

    print(outputText, end="")

def build_replacement_values(
        project: Project,
        project_action: ProjectAction,
        action: Action,
        job: Job,
        inputs: dict[str, str],
        secrets: dict[str, str]
) -> dict[str, SecretableText]:
    replacement_values = {}

    # First loop through all inputs and secrets and perform validation:
    if action.inputs:
        for input_key in action.inputs:
            value = inputs.get(input_key)
            if value is None:
                raise ValueError(
                    f"Input: {input_key} is required by action_type[{project_action.action_type}] action[{project_action.name}]")

    if action.secrets:
        for secret_key in action.secrets:
            value = secrets.get(secret_key)
            if value is None:
                raise ValueError(
                    f"Secret: {secret_key} is required by action_type[{project_action.action_type}] action[{project_action.name}]")

    # Add Inputs required by the action
    if action.pass_all_inputs:
        input_keys_to_pass = inputs.keys()
    else:
        input_keys_to_pass = action.inputs

    if input_keys_to_pass:
        for input_key in input_keys_to_pass:
            input_value = inputs.get(input_key)
            if input_value is None:
                continue

            replacement_values[input_key] = SecretableText(input_value, input_value)

    # Add Secrets required by the action
    if action.pass_all_secrets:
        secret_keys_to_pass = secrets.keys()
    else:
        secret_keys_to_pass = action.secrets

    if secret_keys_to_pass:
        for secret_key in secret_keys_to_pass:
            secret_value = secrets.get(secret_key)
            if secret_value is None:
                continue

            replacement_values[secret_key] = SecretableText(constants.secret_replacement_text, secret_value)

    # Add in action requested environment variables:
    if job.environment:
        for (key, value) in job.environment.items():
            # perform replacement on these as we add them:
            replacement_values[key] = replace_values(value, replacement_values)

    # Add built-in variables:
    replacement_values["CONTAINER_PROJECT_FOLDER"] = text(project.container_project_folder)
    replacement_values["HOST_PROJECT_FOLDER"] = text(project.host_project_folder)
    replacement_values["ACTION_TYPE"] = text(project_action.action_type)
    replacement_values["ACTION"] = text(project_action.name)

    return replacement_values

def replace_values(value: str, replacement_values: dict[str, SecretableText]) -> SecretableText:
    displayable_value = re.sub(r"\${\|(.*?)\|}", lambda match: replace_values_regex(replacement_values, False, match), value)
    secret_value = re.sub(r"\${\|(.*?)\|}", lambda match: replace_values_regex(replacement_values, True, match), value)
    return SecretableText(displayable_value, secret_value)


def replace_values_regex(replacement_values: dict[str, SecretableText], is_secret: bool, match) -> str:
    key = match.group(1)
    if key is None:
        return ""
    value = replacement_values.get(key)
    if value is None:
        return ""
    if is_secret:
        return value.secret_value
    return value.displayable_value


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def norm_relative_path(path: SecretableText) -> SecretableText:
    return SecretableText(norm_relative_path_str(path.displayable_value), norm_relative_path_str(path.secret_value))

def norm_relative_path_str(path: str) -> str:
    return os.path.normpath(path).replace("\\", "/")

