## Why

OpenCICD mounts the host project into containers, so running jobs as the image default user can create files with the wrong ownership on the host. An opt-in CLI flag for the docker runtime user is needed so callers can align container execution with a specific host uid:gid without changing existing behavior.

## What Changes

- Add a new `--docker-user` CLI option that accepts the docker `--user` argument value, such as `1000:1000`.
- Thread the configured docker user through command generation so `docker run` includes `--user <value>` only when the CLI option is provided.
- Update the bundled composite action to pass the current runner uid:gid into `opencicd` so CI-generated docker commands inherit the same runtime ownership behavior.
- Preserve current behavior when `--docker-user` is omitted so generated and executed commands remain unchanged.
- Update the user-facing documentation to explain the new flag, when to use it, and how it affects printed docker commands.

## Capabilities

### New Capabilities
- `docker-runtime-user`: Allow callers to opt into running generated docker containers as a specific docker user value while keeping the default runtime unchanged when no value is supplied.

### Modified Capabilities

## Impact

- CLI argument parsing in `src/opencicd/__main__.py`
- Docker command construction in `src/opencicd/action_runner.py`
- GitHub Action invocation wiring in `action/action.yml`
- Runtime documentation in `docs/running.md` and docker-oriented usage guidance in `docs/action-files.md`
- Targeted tests covering both exec and print command generation paths