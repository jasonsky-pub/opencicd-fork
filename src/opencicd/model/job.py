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
import re
import shlex
from enum import Enum
from typing import Optional

from opencicd.model import serialization
from opencicd.model.serialization import deserialize_enum, deserialize_string_dictionary, deserialize_string_list, \
    deserialize_sub_string


class EntrypointType(Enum):
    Default=0
    Override=1
    Script=2
    Noop=3

class Job:
    def __init__(
        self,
        image: Optional[str],
        dockerfile: Optional[str],
        build_context: Optional[str],
        build_output_file: Optional[str],
        build_output_name_file: Optional[str],
        entrypoint_type: EntrypointType,
        entrypoint_script: Optional[str],
        entrypoint_override: Optional[str],
        arguments: Optional[list[str]],
        environment: Optional[dict[str, str]],
        login_registry: Optional[str],
        login_username: Optional[str],
        login_password: Optional[str],
        push_image: Optional[str],
        push_tags: Optional[str],
        image_file: Optional[str],
        image_name: Optional[str],
        image_name_file: Optional[str],
        volumes: Optional[dict[str, str]]
    ):
        self.image = image
        self.dockerfile = dockerfile
        self.build_context = build_context
        self.build_output_file = build_output_file
        self.build_output_name_file = build_output_name_file
        self.arguments = arguments
        self.entrypoint_type = entrypoint_type
        self.entrypoint_script = entrypoint_script
        self.entrypoint_override = entrypoint_override
        self.environment = environment
        self.login_registry = login_registry
        self.login_username = login_username
        self.login_password = login_password
        self.push_image = push_image
        self.push_tags = push_tags
        self.image_file = image_file
        self.image_name = image_name
        self.image_name_file = image_name_file
        self.volumes = volumes

    def validate(self):
        has_all_login = self.login_username and self.login_password
        has_any_login = self.login_username or self.login_password
        if has_any_login and not has_all_login:
            raise RuntimeError("Must supply all or none of login-username and login-password")

        if self.image is None and self.dockerfile is None and self.image_file is None:
            raise ValueError("Must specify at least one of image, dockerfile or image-file")

        if self.image is not None:
            if self.dockerfile is not None:
                raise ValueError("Cannot specify both image and dockerfile")
            if self.image_file is not None:
                raise ValueError("Cannot specify both image and image_file")
        if self.dockerfile is not None:
            if self.image is not None:
                raise ValueError("Cannot specify both dockerfile and image")
            if self.image_file is not None:
                raise ValueError("Cannot specify both dockerfile and image_file")
        if self.image_file is not None:
            if self.image is not None:
                raise ValueError("Cannot specify both image-file and image")
            if self.dockerfile is not None:
                raise ValueError("Cannot specify both image-file and dockerfile")
            if not self.image_name and not self.image_name_file:
                raise ValueError("Must specify image-name or image-name-file when specifying image-file")
        if self.entrypoint_type == EntrypointType.Default:
            if self.entrypoint_override is not None:
                raise ValueError("Cannot specify entrypoint override if entrypoint type is default")
            if self.entrypoint_script is not None:
                raise ValueError("Cannot specify entrypoint script if type is default")
        if self.entrypoint_type == EntrypointType.Noop:
            if self.entrypoint_override is not None:
                raise ValueError("Cannot specify entrypoint override if entrypoint type is noop")
            if self.entrypoint_script is not None:
                raise ValueError("Cannot specify entrypoint script if type is noop")
            if self.arguments:
                raise ValueError("Cannot specify arguments script if type is noop")
        if self.entrypoint_type == EntrypointType.Script:
            if self.entrypoint_script is None:
                raise ValueError("Must specify entrypoint script if type is script")
            if self.entrypoint_override is not None:
                raise ValueError("Cannot specify entrypoint override if entrypoint type is script")
        if self.entrypoint_type == EntrypointType.Override:
            if self.entrypoint_script is not None:
                raise ValueError("Cannot specify entrypoint script if type is override")
            if self.entrypoint_override is None:
                raise ValueError("Must specify entrypoint override if entrypoint type is override")

    def to_file(self, file_name: str):
        serialization.yaml_to_file(self, file_name)


def from_file(file_name: str) -> Optional[Job]:
    data = serialization.from_yaml_file(file_name)
    if data is None:
        return None
    return deserialize_job(data)


def deserialize_job(data) -> Job:
    arguments = []
    arguments_val = data.get("arguments")
    if arguments_val is not None:
        if isinstance(arguments_val, str):
            arguments = split_quoted_string(arguments_val)
        else:
            arguments = deserialize_string_list(data.get("arguments"), "arguments")

    return Job(
        deserialize_sub_string(data, "image"),
        deserialize_sub_string(data, "dockerfile"),
        deserialize_sub_string(data, "build-context"),
        deserialize_sub_string(data, "build-output-file"),
        deserialize_sub_string(data, "build-output-name-file"),
        deserialize_enum(data.get("entrypoint-type"), EntrypointType),
        deserialize_sub_string(data, "entrypoint-script"),
        deserialize_sub_string(data, "entrypoint-override"),
        arguments,
        deserialize_string_dictionary(data.get("environment"), "environment"),
        deserialize_sub_string(data, "login-registry"),
        deserialize_sub_string(data, "login-username"),
        deserialize_sub_string(data, "login-password"),
        deserialize_sub_string(data, "push-image"),
        data.get("push-tags"),
        deserialize_sub_string(data, "image-file"),
        deserialize_sub_string(data, "image-name"),
        deserialize_sub_string(data, "image-name-file"),
        deserialize_string_dictionary(data.get("volumes"), "volumes")
    )

def deserialize_job_list(data) -> list[Job]:
    jobs = []

    if data is not None:
        for job in data:
            jobs.append(
                deserialize_job(job)
            )

    return jobs

def split_quoted_string(data: str) -> list[str]:
    values = []
    lexer = shlex.shlex(data)
    lexer.wordchars += '!@#$-_:/\\;[]{}|+=()*&^%~'
    for token in lexer:
        # Strip outer quotes only:
        token = re.sub(r"^\"(.*?)\"$", r"\1", token)
        token = re.sub(r"^'(.*?)'$", r"\1", token)
        values.append(token)
    return values
