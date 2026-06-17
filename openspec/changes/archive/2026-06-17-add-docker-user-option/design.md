## Context

OpenCICD currently builds each job's container invocation inside `job_runner()` by assembling a `docker run` command array with fixed runtime flags, volume mounts, environment variables, and optional entrypoint overrides. The CLI parser in `src/opencicd/__main__.py` is the only place where runtime execution options are accepted from users before they are passed into `run_action()`.

This change needs to add an opt-in docker runtime user without changing default behavior for existing callers. The option also needs to appear in `--method print` output so generated commands match executed commands and remain useful in CI systems or scripted invocation.

## Goals / Non-Goals

**Goals:**
- Accept a `--docker-user` CLI option with the same value format docker expects for `docker run --user`.
- Propagate that value through the execution path so every generated `docker run` command includes `--user <value>` only when configured.
- Ensure the bundled composite action forwards the current runner uid:gid into `opencicd` so CI usage benefits from the same ownership behavior without extra caller configuration.
- Keep existing behavior unchanged when the option is omitted.
- Document the new flag clearly in runtime and docker usage documentation.
- Add focused test coverage for command generation with and without the option.

**Non-Goals:**
- Validating or normalizing the docker user string beyond accepting it as CLI text.
- Applying the value to non-runtime docker commands such as `docker build`, `docker image load`, `docker save`, or `docker push`.
- Introducing project-level configuration, action-file syntax, or environment-variable defaults for docker user selection.

## Decisions

1. Add `--docker-user` as a CLI-only execution option.
Rationale: the requested behavior is caller-controlled runtime configuration, not part of a project's action definition. Keeping it in the CLI avoids changing the project model or action schema.

Alternative considered: storing docker user on `Project` or action/job models. Rejected because the value is not intrinsic project metadata and would expand the change into unrelated serialization surfaces.

2. Thread `docker_user: Optional[str]` through `run_action()` into `job_runner()`.
Rationale: command generation happens in `job_runner()`, while argument parsing happens in `async_main()`. Passing an explicit optional parameter keeps the change localized and makes the dependency obvious.

Alternative considered: reading a module-level global or environment variable directly in `action_runner.py`. Rejected because it obscures the execution contract and makes targeted tests harder to write.

3. Insert `--user` into the `docker run` command array before environment variables and the image name.
Rationale: placing it with the other runtime flags preserves the existing command structure and ensures both exec and print methods emit valid docker syntax.

Alternative considered: appending `--user` near the end of the command array. Rejected because it is less readable and risks placing the option after the image boundary if future edits are made carelessly.

4. Cover both printed and executed command assembly paths with narrow tests.
Rationale: the user-facing requirement is about generated docker commands, and the print path is part of the product contract documented in `docs/running.md`. Tests should assert both the default omission case and the opt-in inclusion case.

Alternative considered: docs-only verification. Rejected because this behavior is easy to regress when command assembly changes.

5. Have the composite GitHub Action pass `$(id -u):$(id -g)` into `opencicd --docker-user`.
Rationale: the action is the built-in CI entrypoint for this project, and it already shells out from the runner host before asking `opencicd` to generate docker commands. Forwarding the runner uid:gid there keeps file ownership aligned in the common CI path without changing action-file schema.

Alternative considered: leaving the action unchanged and requiring every workflow author to pass the option manually. Rejected because it leaves the built-in CI entrypoint inconsistent with the intended ownership fix.

## Risks / Trade-offs

- [Call signature churn in `run_action()` and `job_runner()`] -> Mitigation: keep the new parameter optional and update only the direct call sites in `__main__.py`.
- [Users pass an invalid docker user string] -> Mitigation: treat the option as a direct pass-through and rely on docker to validate it, documenting the expected `uid`, `uid:gid`, or named-user formats.
- [Docs drift from actual printed command output] -> Mitigation: update the command examples in `docs/running.md` to show both default behavior and an example with `--docker-user`.
- [Missing test harness around command generation] -> Mitigation: add narrow unit coverage around the command-building path rather than relying on end-to-end docker execution.
- [Composite action runner shells may differ in how `id` is provided] -> Mitigation: keep the implementation to standard `bash` + `id -u` / `id -g`, which matches the action's existing `shell: bash` contract.