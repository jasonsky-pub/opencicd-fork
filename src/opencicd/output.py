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
import json
from enum import Enum

import yaml


class OutputFormat(Enum):
    raw=1
    json=2
    yaml=3

def output_list(data: list[str], format: OutputFormat):
    if format == OutputFormat.raw:
        for item in data:
            print(item)
    elif format == OutputFormat.json:
        print(json.dumps(data, indent=None))
    elif format == OutputFormat.yaml:
        print(yaml.dump(data))

def output(data, format: OutputFormat):
    if format == OutputFormat.raw:
        print(data)
    elif format == OutputFormat.json:
        print(
            json.dumps(
                data,
                default=lambda o:
                    o.name if isinstance(o, Enum) else
                    o.__dict__,
                indent=None
            )
        )
    elif format == OutputFormat.yaml:
        print(yaml.dump(data))

