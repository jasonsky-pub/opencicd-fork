# opencicd

opencicd is a utility that enables the following:

- Projects can specify their technology needs
- A standard interface decoupling projects from ci/cd platforms
- Allowing users to run ci/cd commands locally the same as on the server.
- Simplifying ci/cd orchestration, using docker for everything
- Auto-discovery of ci/cd commands allowing project templates to be a-la-carte

## Installation from pip

To Install:

- Prerequisites: opencicd was developed using Python 3.12, so check that your local python is >= 3.12
- Type in your cli:
  
  ```
  pip install "git+https://github.com/Comcast/OpenCICD.git@main#egg=opencicd"
  ```

## Installation from source

To install from source, download the source and from that directory

```
pip install .
```

## Running opencicd

For info on command line options:

[See Docs](docs/running.md)

## Action Files

For info on Action files options:

[See Docs](docs/action-files.md)

# Creating a Release for opencicd

to create a release:

- As needed update the version in pyproject.toml
- In this folder, run "python -m build"
  - NOTE: If you run into an error "No module named build.__main__", first run "python -m pip install build" and try again
- Commit and push these changes to git before the next step
- Manually Upload the resulting files in "dist" to a new Release in github

# Verifying Installation

After updating run:

```
opencicd --version
```

If it shows the current version, opencicd is installed correctly.

# Installation Troubleshooting

If you run into not being able to run "opencicd" after installing, the pip install location may not be in your path.

- Get the bin path:
  - During install, pip will tell you where it is install to, for example:
    It may install to: ```/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages```
  - Now remove "lib" and everything after it and replace it with bin:
  - ```/Library/Frameworks/Python.framework/Versions/3.11/bin```
- This path needs to be added to your path
  
  ## For Linux/Unix/Mac
  
  using your favorite editor, open ```~/.zshrc``` or ```~/.bash_profile``` depending on which shell you use
  
  ```
  nano ~/.bash_profile
  ```
  
  We need to add the following line at the end: (Make sure to replace the path used)
  
  ```
  export PATH='$PATH:/Library/Frameworks/Python.framework/Versions/3.11/bin'
  ```
  
  ## For windows
  
  Use your system dialog to add a new path for where it installed
