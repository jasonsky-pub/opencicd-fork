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
