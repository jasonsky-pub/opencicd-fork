## 1. CLI plumbing

- [x] 1.1 Add an optional `--docker-user` argument to the CLI parser in `src/opencicd/__main__.py` and capture its value for the current invocation.
- [x] 1.2 Thread the optional docker user value through `run_action()` and `job_runner()` without changing behavior when the option is omitted.

## 2. Docker run generation

- [x] 2.1 Update docker command assembly in `src/opencicd/action_runner.py` so generated `docker run` commands include `--user <value>` only when a docker user was supplied.
- [x] 2.2 Add focused regression coverage for command generation that verifies the `--user` flag is present for opt-in invocations and absent by default.

## 3. Documentation

- [x] 3.1 Update `docs/running.md` to document `--docker-user`, including accepted value examples and `--method print` output that shows the conditional `--user` flag.
- [x] 3.2 Update `docs/action-files.md` to explain when callers may want to use `--docker-user` for mounted project directories and clarify that the option affects runtime `docker run` commands only.

## 4. Composite action integration

- [x] 4.1 Update `action/action.yml` to pass the current bash runner uid:gid into `opencicd --docker-user` so GitHub Action execution uses the same runtime ownership override.