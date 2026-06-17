# Running opencicd
## Simple example
The following is an example command for running the "publish" action for an application:
```
opencicd publish --secret API_KEY=123
```

## Version
To print the ```--version``` and exit
```
opencicd --version
```

## Debug
To turn on debugging, use the ```--debug``` parameter
```
opencicd --debug publish --secret API_KEY=123
```

## List action types
- In order to list the available action types in the project use the ```--list-action-types```:
    ```
    opencicd --list-action-types
    ```
    Output:
    ```
    publish
    ```
- The default output is raw, but yaml and json can be specified with the ```--output-format``` option:
    ```
    opencicd --list-action-types --output-format json
    ```
    Output:
    ```json
    ["publish"]
    ```
  - And Yaml:
    ```
    opencicd --list-action-types --output-format yaml
    ```
    Output:
    ```yaml
    - publish
    ```

## List actions
- Actions available for a type may be listed:
    ```
    opencicd --list-actions publish
    ```
    Output:
    ```
    test
    test2
    ```
The same format options are available as for action types
## Running all Actions of a type:
In order to run all actions of a type, specify the type parameter
```
opencicd --secret API_KEY=123 publish
```
In order to supress output of which job step is being run, specify the ```--quiet``` argument 
```
opencicd --quiet --secret API_KEY=123 publish
```
## Running a specific Action of a type:
In order to run a specific action of a type, specify the type and the action
```
opencicd publish test2
```
example output:
```
opencicd v1.0.18
Processing action-type[publish], action[test2]
Processing action-type[publish], action[test2], job[1]
TEST2!!!
```

## Run Method
Sometimes it is desirable to get the commands to run rather than run the docker commands now by specifying the ```--method print``` option:
```
opencicd --method=print publish test2
```
example output:
```
echo opencicd v1.0.18
set -e
echo "Processing action-type[publish], action[test2]"
echo "Processing action-type[publish], action[test2], job[1]"
"docker" "run" "--rm" "--workdir" "/work" "--volume" ".:/work" "alpine:3.21" "echo" "TEST2!!!" ""
```
The default value for method is ```exec``` which results in running the commands now.

## Posix
Sometimes one is not running on a posix machine (Windows), in such cases ```--no-posix``` can be specified
```
opencicd --method=print --no-posix --quiet publish test2
```
example output:
```
"docker" "run" "--rm" "--workdir" "/work" "--volume" ".:/work" "alpine:3.21" "echo" "TEST2!!!" ""
```
In this scenario, ```set -e``` is not included

## Docker runtime user
If a job writes into the mounted project directory and you need the resulting files to be owned by a specific host user or group, specify ```--docker-user``` with any value accepted by ```docker run --user```, such as ```1000```, ```1000:1000``` or ```node```.

``` 
opencicd --method=print --no-posix --quiet --docker-user 1000:1000 publish test2
```
example output:
```
"docker" "run" "--rm" "--workdir" "/work" "--volume" ".:/work" "--user" "1000:1000" "-e" "CONTAINER_PROJECT_FOLDER=/work" "-e" "HOST_PROJECT_FOLDER=." "-e" "ACTION_TYPE=publish" "-e" "ACTION=test2" "alpine:3.21" "echo" "TEST2!!!" "" "/work" "publish" "test2"
```

If ```--docker-user``` is omitted, generated docker run commands keep using the image default user. This option only affects runtime ```docker run``` commands and does not change ```docker build```, ```docker image load```, ```docker save``` or ```docker push``` commands.

## Temporary runtime home
If a job needs a writable home directory for caches, config files, or temporary state, specify ```--tmp-home``` to mount a disposable tmpfs at ```/tmp/home``` and force ```HOME=/tmp/home``` for generated runtime containers.

```
opencicd --method=print --no-posix --quiet --tmp-home publish test2
```
example output:
```
"docker" "run" "--rm" "--workdir" "/work" "--volume" ".:/work" "--tmpfs" "/tmp/home:rw" "-e" "CONTAINER_PROJECT_FOLDER=/work" "-e" "HOST_PROJECT_FOLDER=." "-e" "ACTION_TYPE=publish" "-e" "ACTION=test2" "-e" "HOME=/tmp/home" "alpine:3.21" "echo" "TEST2!!!" "" "/work" "publish" "test2"
```

When ```--tmp-home``` is combined with a numeric docker runtime user, the generated tmpfs mount inherits the same numeric owner information so that the runtime user can write to ```/tmp/home```.

```
opencicd --method=print --no-posix --quiet --tmp-home --docker-user 1000:1000 publish test2
```
example output:
```
"docker" "run" "--rm" "--workdir" "/work" "--volume" ".:/work" "--user" "1000:1000" "--tmpfs" "/tmp/home:rw,uid=1000,gid=1000" "-e" "CONTAINER_PROJECT_FOLDER=/work" "-e" "HOST_PROJECT_FOLDER=." "-e" "ACTION_TYPE=publish" "-e" "ACTION=test2" "-e" "HOME=/tmp/home" "alpine:3.21" "echo" "TEST2!!!" "" "/work" "publish" "test2"
```

If ```--tmp-home``` is omitted outside ```--cicd```, generated docker run commands keep using the image-defined ```HOME``` behavior. This option only affects runtime ```docker run``` commands and does not change ```docker build```, ```docker image load```, ```docker save``` or ```docker push``` commands.

## Specifying inputs and Secrets

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

## Folders
- Project Folder: This is the folder opencicd can use to access the project (defaults to ```.``` if not specified)
  ```
  opencicd --project-folder /myproject publish
  ```
- Host Project folder: This is the folder the docker commands will be able to find the project on, mostly useful for "--method print" scenarios, defaults to ```.``` 
  ```
  opencicd --project-folder /myproject --host-project-folder /myproject publish
  ```
  This is used as the volume mount source, the docker build folder in docker commands
- Container Project folder: This is the folder the programs in the container will be able to find the project on, defaults to ```\work``` 
  ```
  opencicd --project-folder /myproject --container-project-folder /myproject publish
  ```
  This is used as the volume mount point and workdir inside the container
- Docker runtime user: This is the optional user passed to runtime containers with ```docker run --user```. Use it when mounted files should be written as a specific host uid:gid or named user.
  ```
  opencicd --docker-user 1000:1000 publish
  ```
  If not specified, the image default user is used.

## cicd
When running opencicd from a cicd platform, the ```--cicd``` option does the following:
- All environment variables starting with INPUT_ become inputs, INPUT_PARAM=123 -> PARAM=123
- All environment variables starting with INPUTJSON_ are interpreted as JSON dictionaries and their mappings become inputs 
- All environment variables starting with SECRET_ become inputs, SECRET_PARAM=123 -> PARAM=*****
- All environment variables starting with SECRETJSON_ are interpreted as JSON dictionaries and their mappings become secrets 
- The environment variable DEBUG=true turns on debugging
- The method is defaulted to "print"
- If the environment variable "ACTION_TYPE" is present, it is used as the action-type
- If the environment variable "ACTION" is present, it is used as the action name
- If the environment variable "PROJECT_FOLDER" is present, it is used as the project folder
- If the environment variable "HOST_PROJECT_FOLDER" is present, it is used as the host project folder
- If the environment variable "CONTAINER_PROJECT_FOLDER" is present, it is used as the container project folder
- Tmp-home mode is enabled by default, so generated runtime containers receive ```--tmpfs /tmp/home:rw``` and ```HOME=/tmp/home```
- Specify ```--no-tmp-home``` together with ```--cicd``` to keep the image-defined ```HOME``` behavior
