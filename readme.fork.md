# Fork release instructions

This fork publishes:

- PyPI package: `jsocfork`
- Installed CLI command: `opencicd`
- Docker image: `jasonskypub/jsocfork`

## Release variables

```bash
export VERSION=0.0.1
export IMAGE=jasonskypub/jsocfork
```

## Build the Python package

```bash
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
