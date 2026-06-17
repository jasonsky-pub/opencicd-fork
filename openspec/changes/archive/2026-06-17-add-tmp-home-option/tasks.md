## 1. CLI plumbing

- [x] 1.1 Add a boolean optional `--tmp-home` CLI argument in `src/opencicd/__main__.py` and default it on when `--cicd` is used unless the caller explicitly disables it.
- [x] 1.2 Thread the tmp-home setting through `run_action()` and `job_runner()` alongside the existing docker runtime user option.

## 2. Runtime docker command generation

- [x] 2.1 Update runtime `docker run` command assembly in `src/opencicd/action_runner.py` to add `--tmpfs /tmp/home:rw` when tmp-home mode is enabled.
- [x] 2.2 Add numeric tmpfs ownership options derived from `--docker-user` when the runtime user is supplied as `uid` or `uid:gid`.
- [x] 2.3 Ensure tmp-home mode forces the generated runtime environment to include `HOME=/tmp/home` with precedence over other generated `HOME` values.

## 3. Verification

- [x] 3.1 Add focused command-generation tests that cover explicit `--tmp-home`, default omission outside `--cicd`, cicd default enablement, and `--cicd --no-tmp-home` opt-out behavior.
- [x] 3.2 Add targeted tests that verify numeric `--docker-user` values contribute the expected tmpfs ownership options for `uid` and `uid:gid` cases.

## 4. Documentation

- [x] 4.1 Update `docs/running.md` to document `--tmp-home`, the `/tmp/home` path, the `--cicd` default, opt-out behavior, and the runtime-only scope.
