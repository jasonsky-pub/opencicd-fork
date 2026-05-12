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
from typing import Optional

from opencicd.model import serialization
from opencicd.model.job import Job, deserialize_job_list
from opencicd.model.project import ProjectAction
from opencicd.model.serialization import deserialize_string_list, deserialize_sub_bool, from_yaml_file


class Action:
    def __init__(
        self,
        project_action: ProjectAction,
        inputs: Optional[list[str]],
        secrets: Optional[list[str]],
        dependencies: Optional[list[str]],
        pass_all_inputs: bool,
        pass_all_secrets: bool,
        jobs: list[Job]
    ):
        if jobs is None:
            raise ValueError("jobs cannot be None")
        self.project_action = project_action
        self.inputs = inputs
        self.secrets = secrets
        self.dependencies = dependencies
        self.pass_all_inputs = pass_all_inputs
        self.pass_all_secrets = pass_all_secrets
        self.jobs = jobs

    def to_file(self, file_name: str):
        serialization.yaml_to_file(self, file_name)

    def validate(self):
        if self.inputs and self.pass_all_inputs:
            raise ValueError("inputs and pass_all_inputs cannot both be specified")
        if self.secrets and self.pass_all_secrets:
            raise ValueError("secrets and pass_all_secrets cannot both be specified")

        for job in self.jobs:
            job.validate()

def load_action(project_action: ProjectAction) -> Action:
    data = from_yaml_file(project_action.file_path)
    return deserialize_action(project_action, data)


def deserialize_action(project_action: ProjectAction, data) -> Action:
    return Action(
        project_action,
        deserialize_string_list(data.get("inputs"), "inputs"),
        deserialize_string_list(data.get("secrets"), "secrets"),
        deserialize_string_list(data.get("dependencies"), "dependencies"),
        deserialize_sub_bool(data, "pass-all-inputs"),
        deserialize_sub_bool(data, "pass-all-secrets"),
        deserialize_job_list(data.get("jobs"))
    )
