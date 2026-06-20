# Fork release instructions

This fork publishes:

- PyPI package: `jsocfork`
- Installed CLI command: `opencicd`
- Docker image: `jasonskypub/jsocfork`

## Update from upstream

This fork tracks `../OpenCICD` locally and rebases its fork-specific commits on top of upstream `main`.

```bash
cd /run/media/private/skyzero/random/local/jasonsky-pub/opencicd-fork
git fetch ../OpenCICD main --quiet
git rebase FETCH_HEAD
git push --force-with-lease origin main
```

To review what the fork adds on top of upstream after the rebase:

```bash
cd /run/media/private/skyzero/random/local/jasonsky-pub/opencicd-fork
BASE=$(git merge-base HEAD FETCH_HEAD)
git --no-pager log --reverse --date=short \
  --pretty=format:'%h %ad %s' "$BASE"..HEAD
```

## Fork-specific changes since upstream

Current fork-only commits on top of upstream `main`:

1. `b28fc2d` - Rename the PyPI package from the upstream package name to `jsocfork`, update fork release docs, and keep the installed CLI as `opencicd`.
2. `29c859d` - Update `action/action.yml` to use the fork Docker image `jasonskypub/jsocfork` instead of the upstream image.

## Choose and set the release version

Check the current published PyPI version and the local source version before choosing the next release:

```bash
cd /run/media/private/skyzero/random/local/jasonsky-pub/opencicd-fork

python - <<'PY'
import json
import urllib.request
from pathlib import Path

with urllib.request.urlopen("https://pypi.org/pypi/jsocfork/json", timeout=20) as r:
    data = json.load(r)

print("latest_pypi_version =", data["info"]["version"])
print("all_pypi_versions =", ", ".join(sorted(data.get("releases", {}))))

for line in Path("src/opencicd/__init__.py").read_text(encoding="utf-8").splitlines():
    if line.startswith("__version__ = "):
        print("local_source_version =", line.split("=", 1)[1].strip().strip('"'))
        break
PY
```

Then set the next release version and update the source version before building:

```bash
export VERSION=0.0.4
export IMAGE=jasonskypub/jsocfork

python - <<'PY'
from pathlib import Path
import os
import re

version = os.environ["VERSION"]
path = Path("src/opencicd/__init__.py")
text = path.read_text(encoding="utf-8")
text = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{version}"', text)
text = re.sub(r'__semver__ = "[^"]+"', f'__semver__ = "{version}"', text)
path.write_text(text, encoding="utf-8")
PY
```

## Build the Python package

```bash
rm -rf dist build *.egg-info
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
ls -1 dist/
```

## Publish the Python package to PyPI

```bash
export TWINE_USERNAME=__token__
read -rsp 'PyPI token: ' TWINE_PASSWORD && echo && export TWINE_PASSWORD
python -m twine upload dist/*
```

```bash
python -m pip install --upgrade jsocfork
opencicd --version
```

## Build the Docker image

```bash
docker login
docker build -f src/docker/Dockerfile . \
  -t ${IMAGE}:latest \
  -t ${IMAGE}:${VERSION} \
  --build-arg SEMANTIC_VERSION=${VERSION}
```

## Publish the Docker image

```bash
docker push ${IMAGE}:${VERSION}
docker push ${IMAGE}:latest
```

## Notes

- Keep the PyPI package version and Docker `SEMANTIC_VERSION` aligned for each release.
- Publishing `jsocfork` does not reserve the PyPI name `opencicd`.
- Installing this package still provides the `opencicd` executable.
