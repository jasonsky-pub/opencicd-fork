## ADDED Requirements

### Requirement: CLI supports temporary runtime home option
The `opencicd` CLI SHALL accept an optional `--tmp-home` argument that enables a disposable runtime home directory for generated `docker run` commands in the current invocation.

#### Scenario: Caller provides the tmp-home option
- **WHEN** a caller runs `opencicd` with `--tmp-home`
- **THEN** the invocation SHALL retain tmp-home mode for all generated runtime `docker run` commands in that invocation

#### Scenario: Caller omits the tmp-home option outside cicd mode
- **WHEN** a caller runs `opencicd` without `--tmp-home` and without `--cicd`
- **THEN** the invocation SHALL proceed without configuring a temporary runtime home override

### Requirement: Runtime docker commands configure a temporary home mount
OpenCICD SHALL add a tmpfs mount at `/tmp/home` and SHALL set `HOME=/tmp/home` for each generated runtime `docker run` command when tmp-home mode is enabled.

#### Scenario: Printed commands include tmpfs and home override
- **WHEN** a caller runs `opencicd --method print --tmp-home`
- **THEN** each printed runtime `docker run` command SHALL include `--tmpfs` followed by `/tmp/home:rw`
- **THEN** each printed runtime `docker run` command SHALL include `-e` followed by `HOME=/tmp/home`

#### Scenario: Tmp-home overrides other generated home values
- **WHEN** tmp-home mode is enabled for a runtime `docker run` command
- **THEN** the generated command SHALL set `HOME=/tmp/home` even if other generated environment mappings would otherwise set `HOME` to a different value

### Requirement: Temporary home ownership aligns with numeric docker user values
When tmp-home mode is enabled and a docker runtime user is configured as `uid` or `uid:gid`, OpenCICD SHALL configure the tmpfs mount ownership to match the numeric user information supplied for `--docker-user`.

#### Scenario: Docker user supplies uid only
- **WHEN** a caller runs `opencicd --tmp-home --docker-user 1000`
- **THEN** each generated runtime `docker run` command SHALL configure the tmpfs mount so `/tmp/home` is owned by uid `1000`

#### Scenario: Docker user supplies uid and gid
- **WHEN** a caller runs `opencicd --tmp-home --docker-user 1000:1001`
- **THEN** each generated runtime `docker run` command SHALL configure the tmpfs mount so `/tmp/home` is owned by uid `1000` and gid `1001`

### Requirement: Cicd mode enables tmp-home by default
OpenCICD SHALL enable tmp-home mode by default for generated runtime `docker run` commands when the caller uses `--cicd`.

#### Scenario: Cicd-generated commands use temporary home
- **WHEN** a caller runs `opencicd --cicd`
- **THEN** generated runtime `docker run` commands SHALL include the tmp-home tmpfs mount and `HOME=/tmp/home`

#### Scenario: Caller disables cicd tmp-home default
- **WHEN** a caller runs `opencicd --cicd --no-tmp-home`
- **THEN** generated runtime `docker run` commands SHALL omit the tmp-home tmpfs mount
- **THEN** generated runtime `docker run` commands SHALL omit the generated `HOME=/tmp/home` override

### Requirement: Documentation explains temporary runtime home behavior
The user-facing documentation SHALL describe `--tmp-home`, the `/tmp/home` runtime path, the `--cicd` default, and the fact that the option affects generated runtime `docker run` commands only.

#### Scenario: Runtime documentation shows tmp-home behavior
- **WHEN** a user reads the documented CLI runtime options
- **THEN** the documentation SHALL include an example that uses `--tmp-home`
- **THEN** the documentation SHALL explain that `--cicd` enables tmp-home by default
- **THEN** the documentation SHALL explain that the option does not affect non-runtime docker commands