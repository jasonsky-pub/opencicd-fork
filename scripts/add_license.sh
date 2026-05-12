#!/bin/bash

# Add License Headers to all Python files in the src directory
# Reference: https://pypi.org/project/licenseheaders/


# Install the licenseheaders package if not already installed. Please install them manually
# pip install --quiet licenseheaders

# Add license headers using the LICENSE file in the root directory for python files
python -m licenseheaders -t ../LICENSE -d ../src --ext py

# Update the current in the LICENSE file in the root directory for python files
# python -m licenseheaders -cy -d ../src --ext py

# Add license headers using the LICENSE file in the root directory for docker files
python -m licenseheaders -t ../LICENSE -d ../src --ext Dockerfile
# Update the current in the LICENSE file in the root directory
# python -m licenseheaders -cy -d ../src --ext Dockerfile

# Add license headers using the LICENSE file in the root directory for YAML files
python -m licenseheaders -t ../LICENSE --ext .yaml

# Add license headers using the LICENSE file in the root directory for yml files
python -m licenseheaders -t ../LICENSE --ext .yml