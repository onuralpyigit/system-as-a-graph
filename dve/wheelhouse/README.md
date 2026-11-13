# dve wheelhouse

Wheels of `dve`'s dependencies (Flask + Werkzeug, Jinja2, MarkupSafe,
itsdangerous, click, blinker, importlib-metadata, zipp, Flask-WTF,
WTForms) for offline install. Needs CPython 3.9, x86_64, glibc >= 2.17
(CentOS 7+).

`mdg` is a local dependency, not vendored here; install it first. From
the repository root:

```bash
python3 -m venv venv && source venv/bin/activate
pip install --no-build-isolation --no-index --find-links=mdg/wheelhouse ./mdg
pip install --no-build-isolation --no-index --find-links=dve/wheelhouse ./dve
```

Regenerate where PyPI is reachable:

```bash
python3 -m pip download --dest dve/wheelhouse --only-binary=:all: \
  --python-version 3.9 --implementation cp \
  --platform manylinux2014_x86_64 --platform manylinux_2_28_x86_64 \
  --abi cp39 --abi abi3 "Flask==2.3.2" "Flask-WTF==1.2.2"
```
