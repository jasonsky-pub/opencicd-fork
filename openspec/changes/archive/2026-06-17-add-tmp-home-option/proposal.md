## Why

Some containerized jobs need a writable home directory for caches, config files, or temporary state, but writing that data into the mounted project folder can pollute the checkout and create ownership issues. OpenCICD needs an opt-in runtime home mode that directs `HOME` to disposable storage and becomes the default when generating CI commands via `--cicd`.

## What Changes

- Add a new optional `--tmp-home` CLI flag that configures generated runtime `docker run` commands to mount a temporary writable home directory and set `HOME` to that location.
- Make `--tmp-home` take precedence over any other generated `HOME` environment value for runtime containers so the disposable home location is deterministic.
- When `--docker-user` is supplied with `uid` or `uid:gid`, use the same numeric owner information for the temporary home mount so the runtime user can write to it.
- Update `--cicd` defaults so CI-generated commands automatically enable `--tmp-home` unless a caller explicitly disables it.
- Preserve current runtime behavior for non-`--cicd` invocations when `--tmp-home` is omitted.
- Document the runtime scope, ownership behavior, and CI defaulting of the new option.

## Capabilities

### New Capabilities
- `docker-runtime-tmp-home`: Allow callers to opt into a disposable runtime home directory for generated `docker run` commands, with CI defaulting and owner alignment for numeric `--docker-user` values.

### Modified Capabilities

## Impact

- CLI argument parsing and `--cicd` defaulting in `src/opencicd/__main__.py`
- Runtime docker command construction in `src/opencicd/action_runner.py`
- GitHub Action and CI documentation in `action/action.yml` and `docs/running.md`
- Targeted command-generation tests covering tmp-home behavior, precedence, and numeric docker-user ownership handling