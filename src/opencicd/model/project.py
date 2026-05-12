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
import os
import re
from typing import Optional, Tuple

from opencicd import constants
from opencicd.model.serialization import raw_from_file


class ProjectAction:
    def __init__(
        self,
        action_type: str,
        name: str,
        file_path: str
    ):
        if action_type is None:
            raise ValueError('action_type is required')
        if name is None:
            raise ValueError('name is required')
        if file_path is None:
            raise ValueError('file_path is required')

        self.action_type = action_type
        self.name = name
        self.file_path = file_path

class Project:
    def __init__(
        self,
        project_folder: str,
        host_project_folder: str,
        container_project_folder: str
    ):
        if project_folder is None:
            raise TypeError("project_folder is required")
        if host_project_folder is None:
            raise TypeError("host_project_folder is required")
        if container_project_folder is None:
            raise TypeError("container_project_folder is required")

        self.project_folder = project_folder
        self.host_project_folder = host_project_folder
        self.container_project_folder = container_project_folder

    def get_cicd_ignore_files(self) -> list[str]:
        open_cicd_folder = self.get_opencicd_folder()
        filepath = ".cicdignore"
        file_path = os.path.join(open_cicd_folder, filepath)
        if not os.path.exists(file_path):
            return []

        ignore_file = raw_from_file(os.path.abspath(file_path))
        ignore_files = ignore_file.split("\n")
        return [file.strip() for file in ignore_files]

    def get_opencicd_folder(self) -> str:
        return os.path.join(self.project_folder, constants.project_config_folder_name)

    def get_actions(self) -> dict[str: list[ProjectAction]]:
        open_cicd_folder = self.get_opencicd_folder()
        if not os.path.exists(open_cicd_folder):
            return {}

        if not os.path.isdir(open_cicd_folder):
            raise FileExistsError("File exists where folder expected: " + open_cicd_folder)

        files = os.listdir(open_cicd_folder)

        actions = {}
        ignore_files = self.get_cicd_ignore_files()

        for file in files:
            is_ignore_file = False
            for ignore_file in ignore_files:
                if re.match(ignore_file, file):
                    is_ignore_file = True
                    break

            if is_ignore_file:
                logging.debug("Ignoring file: " + file + " matched by .cicdignore")
                continue

            result = interpret_action_filename(file)
            if result is None:
                continue
            (action_type, name) = result

            file_path = os.path.join(open_cicd_folder, file)

            cur_actions = actions.get(action_type)
            if cur_actions is None:
                cur_actions = []

            action = ProjectAction(action_type, name, os.path.abspath(file_path))
            cur_actions.append(action)
            actions[action_type] = cur_actions

        return actions


def interpret_action_filename(file_name: str) -> Optional[Tuple[str, str]]:
    basename = os.path.basename(file_name)

    match = re.match("^([^.]*?)\.(.*?).action.yaml$", basename)
    if not match:
        return None

    return match.group(1), match.group(2)

