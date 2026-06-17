## Context

OpenCICD currently assembles runtime `docker run` commands in `job_runner()` within `src/opencicd/action_runner.py`. The CLI in `src/opencicd/__main__.py` is responsible for parsing execution options, choosing `--cicd` defaults, and threading runtime configuration into `run_action()`.

The new tmp-home behavior is cross-cutting because it affects command-line option parsing, `--cicd` defaults, environment generation, and runtime docker flags. It also needs to cooperate with the already-supported `--docker-user` option so non-root runtime users can write to the temporary home directory without changing existing behavior for callers who do not opt in.

## Goals / Non-Goals

**Goals:**
- Add a caller-facing `--tmp-home` execution option that enables a disposable home directory for runtime containers.
- Make `--cicd` enable tmp-home by default while still allowing callers to disable the behavior explicitly.
- Ensure generated runtime commands add both the tmpfs mount and a deterministic `HOME=/tmp/home` override.
- Reuse numeric `--docker-user` values to set tmpfs ownership so non-root runtime users can write to `/tmp/home`.
- Keep the behavior limited to runtime `docker run` commands and preserve current defaults for non-`--cicd` invocations that do not request tmp-home.

**Non-Goals:**
- Changing action-file schema to declare tmp-home behavior per job.
- Changing the existing docker runtime user option format or validating non-numeric user strings beyond the current pass-through behavior.
- Applying tmp-home behavior to `docker build`, `docker image load`, `docker save`, or `docker push` commands.
- Making the temporary home path configurable in this change.

## Decisions

1. Add `--tmp-home` as a boolean optional CLI flag and default it to enabled only under `--cicd`.
Rationale: tmp-home is an execution policy, not project metadata. A boolean optional flag keeps the caller contract explicit and allows `--cicd --no-tmp-home` to opt out of the CI default without adding more action-level inputs.

Alternative considered: hard-coding tmp-home for all `--cicd` runs with no opt-out. Rejected because it makes CI behavior less transparent and leaves no clean escape hatch for workflows that rely on an image-defined `HOME`.

2. Thread tmp-home configuration through `run_action()` and `job_runner()` alongside `docker_user`.
Rationale: runtime command assembly already receives caller-controlled execution settings through explicit parameters. Keeping tmp-home as another optional parameter localizes the change and avoids broad model or serialization updates.

Alternative considered: deriving tmp-home directly from environment variables inside `action_runner.py`. Rejected because it hides the execution contract and makes focused tests harder to write.

3. Represent tmp-home with fixed runtime outputs: `--tmpfs /tmp/home:rw...` and `-e HOME=/tmp/home`.
Rationale: the user request is for a disposable runtime home with a stable path. A fixed path keeps the documentation, tests, and generated commands simple and makes precedence unambiguous.

Alternative considered: deriving `HOME` from `CONTAINER_PROJECT_FOLDER` or host shell `HOME`. Rejected because the desired behavior is specifically a disposable runtime home, not a workspace home or forwarded host environment.

4. Derive tmpfs ownership options from numeric `--docker-user` values only.
Rationale: Docker tmpfs ownership uses uid/gid numbers. When `--docker-user` is `uid` or `uid:gid`, OpenCICD can safely add matching ownership options to the tmpfs mount. Non-numeric user strings remain pass-through for `--user`, but tmpfs ownership cannot be inferred reliably from them without extra container introspection.

Alternative considered: requiring `--docker-user` to always be numeric when `--tmp-home` is used. Rejected because it would narrow the existing docker-user contract more than the requested change requires.

5. Force the generated `HOME=/tmp/home` mapping to win over other generated environment values.
Rationale: tmp-home mode is only useful if home-relative writes are deterministic. The command builder should therefore emit the tmp-home `HOME` mapping in a way that overrides earlier generated values from inputs or job environment configuration.

Alternative considered: documenting that callers must avoid setting `HOME` themselves when using tmp-home. Rejected because it is error-prone and leaves behavior ambiguous.

## Risks / Trade-offs

- [Command assembly grows another optional runtime branch] -> Mitigation: keep tmp-home generation adjacent to the existing `--user` logic and cover it with narrow print-path tests.
- [Non-numeric docker user strings cannot be translated into tmpfs owner options] -> Mitigation: document that ownership alignment only applies to numeric `uid` or `uid:gid` values while leaving `--user` pass-through unchanged.
- [Generated `HOME=/tmp/home` can override a user-supplied `HOME` job environment value] -> Mitigation: treat that precedence as the explicit contract of tmp-home mode and document the opt-out path via `--no-tmp-home`.
- [Tmpfs behavior is Linux/Docker-runtime specific] -> Mitigation: scope the behavior to generated docker runtime commands and document it as part of the docker invocation contract rather than a platform-neutral filesystem feature.

## Migration Plan

1. Add the CLI flag and cicd defaulting behavior.
2. Thread tmp-home settings into runtime command generation and add tmpfs ownership parsing for numeric docker-user values.
3. Extend command-generation tests to cover explicit enablement, cicd defaults, opt-out, and numeric ownership options.
4. Update runtime documentation and CI-oriented usage guidance.

Rollback strategy: remove the tmp-home flag plumbing and command-generation branch, which restores the existing image-defined `HOME` behavior and leaves `--docker-user` unchanged.

## Open Questions

- Should tmpfs ownership for `--docker-user <uid>` set only `uid=<uid>` or set both `uid=<uid>` and `gid=<uid>` for symmetry? The current proposal only requires uid alignment when gid is omitted.
- Should the implementation use `--tmpfs` exactly as requested or prefer `--mount type=tmpfs` for readability? The proposal currently stays with `--tmpfs` to match the requested command shape.