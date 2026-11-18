# mdg wheelhouse

Wheels of `mdg`'s dependencies (PyMySQL[rsa] + cryptography, cffi,
pycparser, PyYAML) for offline install. Needs CPython 3.9, x86_64, glibc >= 2.17
(CentOS 7+).

Install from the repository root:

```bash
python3 -m venv venv && source venv/bin/activate
pip install --no-build-isolation --no-index --find-links=mdg/wheelhouse ./mdg
```

Regenerate where PyPI is reachable:

```bash
python3 -m pip download --dest mdg/wheelhouse --only-binary=:all: \
  --python-version 3.9 --implementation cp \
  --platform manylinux2014_x86_64 --platform manylinux_2_28_x86_64 \
  --abi cp39 --abi abi3 "PyMySQL[rsa]==1.0.3" "PyYAML==6.0"
```
