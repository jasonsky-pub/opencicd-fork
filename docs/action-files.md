# Action Files

## General
- All action files live under the ```.opencicd``` folder in the project
- The name of the file dictates the "Action Name" and "Action Type".
  - The format is: ```[Action.Name].[ActionType].action.yaml```
  - The Action Name may have dots in it
  - The ActionType may not have dots in it 
- Files are automatically discovered by filename

## Ignore action files:
In order to ignore a file in the .opencicd folder, create the file ```.opencicd/.cicdignore```:
```
test3\.publish\.action\.yaml
```
NOTE: This file uses regular expressions (one per line), this is why the dots are escaped above

# File Format
The action file is a yaml file with the following elements
## Input
Inputs which are required by this action are designated as such:
```yaml
inputs:
  - INPUT1
  - INPUT2
```
No other inputs other than the ones specified will be provided

### Built-In Variables
The following variables are available and will always overwrite input/secret values if supplied with the same key:
- The input ```CONTAINER_PROJECT_FOLDER``` is the container project root
- The input ```HOST_PROJECT_FOLDER``` is the host project root
- The input ```ACTION_TYPE``` is the currently running action type
- The input ```ACTION``` is the currently running action name

## Send all inputs
In order to send all inputs to the action jobs, specify:
```yaml
pass-all-inputs: true
```
You cannot specify both pass-all-inputs and inputs at the same time
## Secrets
Secrets which are required by this action are designated as such:
```yaml
secrets:
  - INPUT1
  - INPUT2
```
No other secrets other than the ones specified will be provided
## Send all secrets
In order to send all secrets to the action jobs, specify:
```yaml
pass-all-secrets: true
```
You cannot specify both pass-all-secrets and secrets at the same time
## Replacements
In most properties below, replacements can be used such as these:
```yaml
arguments: echo "${|INPUT1|}"
```
This will replace the Input, Secret or Environment variable with the name INPUT1 

## Dependencies
Sometimes one build output relies on another.  In this case, an action file may declare "dependencies" on other action files.  This is done like so:
```yaml
dependencies:
  - action1
  - action2.name.here
```
If the current action is named ```action3.publish.yaml```:
- it's name is ```action3```
- and it requires ```action1.publish.yaml``` and ```action2.name.here.publish.yaml```

This only applies when running an entire action-type, however when invoked directly the dependencies are ignored.

# Jobs
Jobs are a list of docker commands to be run when running this action, ex:
```yaml
jobs:
    - image: alpine:latest
      arguments: echo "${|INPUT1|}"
```
## Step 1: Image
You may specify one of the following to designate the docker image to use:
- Pre-built Image to run:
  ```yaml
  - image: alpine:latest
    arguments: echo "${|INPUT1|}"
  ```
  NOTE: Replacements for inputs, secrets and environment variables are made here are made. 
- Dockerfile to build:
  - This will build AND run a dockerfile:
    ```yaml
    - dockerfile: dockerfiles/myapp.dockerfile
      arguments: echo "${|INPUT1|}"
    ```
  - **BUILD CONTEXT**: For building a dockerfile, by default the build-context is the project's root folder.  If instead you wish to change this the "build-context" can be specified.  The "build-context" is relative to the project root folder.
    ```yaml
    -   dockerfile: .opencicd/publish-test.dockerfile
        entrypoint-type: noop
        build-context: .opencicd
    ```
  - This will build but not RUN the dockerfile, while writing the image to a file:
    ```yaml
    -   dockerfile: .opencicd/publish-test.dockerfile
        entrypoint-type: noop
        build-output-file: dist/output.tar
        build-output-name-file: dist/output.name.txt
    ```
    This will create two files, one with the build output and one file containing the name of the image (since there is no clean way to get this).
  
- Image File: an archive containing an image:
  ```yaml
  - image-file: dist/image-file.tar
    image-name-file: dist/image-name.txt
    arguments: echo "${|INPUT1|}"
  ```
  or 
  ```yaml
  - image-file: dist/image-file.tar
    image-name: "image-name-here"
    arguments: echo "${|INPUT1|}"
  ```
  Note, in this case, there is no clean way to "detect" the loaded image name, so either the image-name or file with the image-name in it (image-name-file) must be specified  

## Step 2: Entrypoint
You may only specify one of the following entrypoint types at a time:
- **Default**: run the default entrypoint in the docker image.
  - Not specified means "default":
    ```yaml
    - image: alpine:latest
    ```
  - Or explicitly mention:
    ```yaml
    - image: alpine:latest
      entrypoint-type: default
    ```
- **Override**: run a specific executable/script in the docker
  ```yaml
  - image: alpine:latest
    entrypoint-type: override
    entrypoint-override: bash
  ```
- **Script**: run a specific script from the project inside the docker:
  ```yaml
  - image: alpine:latest
    entrypoint-type: script
    entrypoint-script: scripts/myscript.sh
  ```
  NOTE: in order to run this, the "sh" shell must exist on the destination docker as it is used to invoke the executable/script. Also, scripts should be declared with it's own interpreter in the "#!" line)
  Also, the path is relative to the project root.
- **Noop**: In cases such as building or pushing a docker image, you may not actually want to run it:
  ```yaml
  - image: alpine:latest
    entrypoint-type: noop
  ```
  This will technically pull the image but not run it

### Arguments
After the entrypoint is specified, arguments may be supplied in two ways:
- As a string 
  ```yaml
  jobs:
      - image: alpine:latest
        arguments: echo "${|INPUT1|}"
  ```
- Or as a list (needed sometimes):
  ```yaml
  jobs:
      - image: alpine:latest
        arguments:
          - echo
          - "${|INPUT1|}"
  ```
Arguments are passed to all entrypoint types except noop.

### Environment
You can set up specific environment variables for a job like so:
```yaml
  -   image: "alpine:${|ALPINE_VERSION|}"
      arguments: echo hi from alpine:${|ALPINE_VERSION|}
      environment:
          ALPINE_VERSION: 3.21
```

### Volumes
You can specify volumes to mount when RUNNING the image just like typically done with the "docker run --volume X:Y" option
```yaml
  -   image: "alpine:${|ALPINE_VERSION|}"
      arguments: echo hi from alpine:${|ALPINE_VERSION|}
      volumes:
          "/tmp": "/var/test-${|ALPINE_VERSION|}"
      environment:
          ALPINE_VERSION: 3.21
```
NOTE: Replacements are made in both the key and the value

# Step 3: Pushing an image
After the image is loaded and possibly run, the image can be pushed like so:
```yaml
jobs:
    - image: alpine:latest
      push-image: "ghcr.io/example-org/my-image-name"
      push-tags: "${|RELEASE_VERSION|},latest"
```
This will pull the alpine image, run it and push it to github packages

# Docker login
In some cases docker login will be required.  In such cases, you will need to specify three parameters:
```yaml
jobs:
    - image: my-registry.com/my-image:latest
      login-registry: "ghcr.io"
      login-username: "${|USERNAME_SECRET_HERE|}"
      login-password: "${|PASSWORD_SECRET_HERE|}"
```
The same login information will be used for pull and push
