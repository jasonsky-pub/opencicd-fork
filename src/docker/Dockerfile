##
##              Copyright 2025 Comcast Cable Communications Management, LLC
##
##              Licensed under the Apache License, Version 2.0 (the "License");
##              you may not use this file except in compliance with the License.
##              You may obtain a copy of the License at
##
##              http://www.apache.org/licenses/LICENSE-2.0
##
##              Unless required by applicable law or agreed to in writing, software
##              distributed under the License is distributed on an "AS IS" BASIS,
##              WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##              See the License for the specific language governing permissions and
##              limitations under the License.
##
##              SPDX-License-Identifier: Apache-2.0
##
##              This product includes software developed at Comcast (https://www.comcast.com/).##

FROM alpine:3.22.4
ARG SEMANTIC_VERSION

RUN apk update
RUN apk add --update python3 py3-pip bash
RUN mkdir -p /tmp/build

WORKDIR /tmp/build
COPY . .

# get the python package version
RUN pip3 install --break-system-packages packaging

WORKDIR /tmp/build
# Update project version file
ENV initfile="src/opencicd/__init__.py"
RUN PACKAGE_VERSION="$(python3 -c "from packaging.version import Version; print(Version('$SEMANTIC_VERSION'))")" && \
    grep -v -E "__version__|__semver__" "$initfile" > "${initfile}.new" && \
    mv "${initfile}.new" "$initfile" && \
    printf "\n__version__ = \"%s\"\n__semver__ = \"%s\"\n\n" "$PACKAGE_VERSION" "$SEMANTIC_VERSION" >> "$initfile"

# build
RUN pip3 install --break-system-packages .
RUN rm -rf /tmp/build

ENTRYPOINT ["opencicd"]
