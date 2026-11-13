# Digital System Model

- `mdg`: DSM-MDG, Model Data Generator. A library producing the Model
  Setup Data file of a selected project, platform and system version.
- `dve`: DSM-DVE, Design Verification Engine. A Flask API running
  mdg productions in child processes, and a browser UI over mdg.

Requirements: `docs/SRS.md`.

## Run

Settings: `mdg/src/mdg/mdg.ini`, `dve/src/dve/dve.ini`.

**1. Mock data sources** (MySQL and Gitea):

```bash
cd dev && docker compose up
```

**2. Packages** (into a venv):

```bash
python3 -m venv venv && source venv/bin/activate
pip install -e ./mdg -e ./dve
```

Without PyPI access, install from the vendored wheels instead:
`mdg/wheelhouse/README.md`, `dve/wheelhouse/README.md`.

**3. API** (Ctrl+C stops it and its runs):

```bash
dsm
```

**4. UI:** <http://127.0.0.1:8080>, sign in as `admin` / `admin`, connect both data sources as `dsm` / `dsm`.

## Test

```bash
cd mdg && python3 -m pytest
cd dve && python3 -m pytest
```
