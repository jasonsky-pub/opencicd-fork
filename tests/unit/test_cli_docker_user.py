import asyncio
from pathlib import Path

import pytest

from opencicd.__main__ import async_main


pytestmark = pytest.mark.unit

TEST_PROJECT_DIR = Path(__file__).resolve().parents[2] / "test"


def run_print_command(capsys: pytest.CaptureFixture[str], *extra_args: str) -> list[str]:
    asyncio.run(
        async_main(
            [
                "opencicd",
                "--project-folder",
                str(TEST_PROJECT_DIR),
                "--host-project-folder",
                ".",
                "--method=print",
                "--no-posix",
                "--quiet",
                *extra_args,
                "publish",
                "test2",
            ]
        )
    )
    return [line for line in capsys.readouterr().out.splitlines() if line.startswith('"docker" "run"')]


def test_print_commands_include_docker_user_when_requested(capsys: pytest.CaptureFixture[str]):
    run_lines = run_print_command(capsys, "--docker-user", "1000:1000")

    assert run_lines
    assert all('"--user" "1000:1000"' in line for line in run_lines)
    assert '"--user" "1000:1000"' in run_lines[0]
    assert run_lines[0].index('"--user" "1000:1000"') < run_lines[0].index('"alpine:3.21"')


def test_print_commands_omit_docker_user_by_default(capsys: pytest.CaptureFixture[str]):
    run_lines = run_print_command(capsys)

    assert run_lines
    assert all('"--user"' not in line for line in run_lines)


def test_print_commands_include_tmp_home_when_requested(capsys: pytest.CaptureFixture[str]):
    run_lines = run_print_command(capsys, "--tmp-home")

    assert run_lines
    assert all('"--tmpfs" "/tmp/home:rw"' in line for line in run_lines)
    assert all('"-e" "HOME=/tmp/home"' in line for line in run_lines)


def test_print_commands_omit_tmp_home_by_default(capsys: pytest.CaptureFixture[str]):
    run_lines = run_print_command(capsys)

    assert run_lines
    assert all('"--tmpfs"' not in line for line in run_lines)
    assert all('"HOME=/tmp/home"' not in line for line in run_lines)


def test_cicd_print_commands_enable_tmp_home_by_default(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACTION_TYPE", "publish")
    monkeypatch.setenv("ACTION", "test2")
    monkeypatch.setenv("PROJECT_FOLDER", str(TEST_PROJECT_DIR))
    monkeypatch.setenv("HOST_PROJECT_FOLDER", ".")
    monkeypatch.setenv("CONTAINER_PROJECT_FOLDER", "/work")

    asyncio.run(
        async_main(
            [
                "opencicd",
                "--cicd",
                "--no-posix",
                "--quiet",
            ]
        )
    )

    run_lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith('"docker" "run"')]

    assert run_lines
    assert all('"--tmpfs" "/tmp/home:rw"' in line for line in run_lines)
    assert all('"-e" "HOME=/tmp/home"' in line for line in run_lines)


def test_cicd_print_commands_can_disable_tmp_home(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACTION_TYPE", "publish")
    monkeypatch.setenv("ACTION", "test2")
    monkeypatch.setenv("PROJECT_FOLDER", str(TEST_PROJECT_DIR))
    monkeypatch.setenv("HOST_PROJECT_FOLDER", ".")
    monkeypatch.setenv("CONTAINER_PROJECT_FOLDER", "/work")

    asyncio.run(
        async_main(
            [
                "opencicd",
                "--cicd",
                "--no-tmp-home",
                "--no-posix",
                "--quiet",
            ]
        )
    )

    run_lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith('"docker" "run"')]

    assert run_lines
    assert all('"--tmpfs"' not in line for line in run_lines)
    assert all('"HOME=/tmp/home"' not in line for line in run_lines)


def test_print_commands_include_tmp_home_uid_owner_from_docker_user(capsys: pytest.CaptureFixture[str]):
    run_lines = run_print_command(capsys, "--tmp-home", "--docker-user", "1000")

    assert run_lines
    assert all('"--tmpfs" "/tmp/home:rw,uid=1000"' in line for line in run_lines)


def test_print_commands_include_tmp_home_uid_gid_owner_from_docker_user(capsys: pytest.CaptureFixture[str]):
    run_lines = run_print_command(capsys, "--tmp-home", "--docker-user", "1000:1001")

    assert run_lines
    assert all('"--tmpfs" "/tmp/home:rw,uid=1000,gid=1001"' in line for line in run_lines)