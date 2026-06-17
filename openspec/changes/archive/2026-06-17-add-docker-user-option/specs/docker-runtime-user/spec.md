## ADDED Requirements

### Requirement: CLI supports docker runtime user option
The `opencicd` CLI SHALL accept an optional `--docker-user` argument and SHALL treat its value as the docker runtime user for the current invocation.

#### Scenario: Caller provides a docker user value
- **WHEN** a caller runs `opencicd` with `--docker-user 1000:1000`
- **THEN** the invocation SHALL retain `1000:1000` as the docker runtime user for all generated `docker run` commands in that invocation

#### Scenario: Caller omits the docker user value
- **WHEN** a caller runs `opencicd` without `--docker-user`
- **THEN** the invocation SHALL proceed without configuring a docker runtime user override

### Requirement: Docker run commands honor the configured runtime user
OpenCICD SHALL add `--user <value>` to each generated `docker run` command only when a docker runtime user is configured for the invocation.

#### Scenario: Printed commands include the docker user
- **WHEN** a caller runs `opencicd --method print --docker-user 1000:1000`
- **THEN** each printed `docker run` command SHALL include `--user` followed by `1000:1000`
- **THEN** the `--user` option SHALL appear before the image name in the printed command

#### Scenario: Default commands omit the docker user
- **WHEN** a caller runs `opencicd` without `--docker-user`
- **THEN** generated `docker run` commands SHALL omit the `--user` option

### Requirement: Documentation explains docker runtime user behavior
The user-facing CLI documentation SHALL describe the `--docker-user` option, its expected value format, and the fact that it affects generated `docker run` commands only when provided.

#### Scenario: Runtime documentation shows opt-in usage
- **WHEN** a user reads the documented CLI runtime options
- **THEN** the documentation SHALL include an example that uses `--docker-user`
- **THEN** the documentation SHALL explain that omitting the option preserves the current default behavior

### Requirement: Composite action forwards runner uid and gid
The bundled GitHub composite action SHALL invoke `opencicd` with `--docker-user <uid>:<gid>` using the current bash runner user's uid and gid.

#### Scenario: Composite action generates commands for CI execution
- **WHEN** the bundled composite action runs `opencicd` in CI
- **THEN** it SHALL pass the current runner uid and gid to `--docker-user`
- **THEN** generated runtime `docker run` commands SHALL inherit that uid:gid override