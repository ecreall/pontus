# Worklog

Running log of the work on this repository, newest first.
Version française : [`../fr/worklog.md`](../fr/worklog.md).

## 2026-07-13

- Forked `ecreall/pontus` to `michaellaunay/pontus`; maintenance resumed by
  Michaël Launay (Logikascium).
- Converted `README.rst` and `CHANGES.rst` to Markdown; rewrote the README
  with the repository status and the modernisation roadmap.
- Updated build metadata (`setup.py`: fork URLs, maintainer field, Markdown
  long description, Python 3.6 classifier); added a minimal PEP 518
  `pyproject.toml`; updated `MANIFEST.in`.
- Added `constraints-legacy.txt` (known-good 2017 dependency pins) and a
  best-effort legacy CI workflow (`python:3.6-buster`, `ecreall_dace`
  installed from its maintained fork).
- Established the bilingual documentation structure (`docs/en`, `docs/fr`)
  and this worklog.
- Preventively applied the era-compatibility fixes learned from dace's first
  two CI runs, before pontus' own first run: `setuptools<46` (the 2016/2017
  sdists still use the `Feature` API removed in setuptools 46), apt repointed
  to archive.debian.org (buster archived in 2024), `libzmq3-dev` (pyzmq
  14.4.1, via ecreall_dace, has no Python 3.6 wheel), `actions/checkout`
  bumped to v5, and `mock` shipped in the `[test]` extra (substanced's
  venusian scan imports its own test modules at Configurator setup).
- Added `libjpeg-dev` and `zlib1g-dev`: Pillow 3.4.2 predates Python 3.6
  wheels (verified on PyPI) and must be built from source.


## 2026-07-14

- Removed the dead upstream `cryptacular` C dependency from the CI
  environment (it was never pinned: pip was silently building the 1.6.2
  sdist). The maintained drop-in rewrite (`michaellaunay/cryptacular` 2.x,
  PyCA bcrypt + hashlib backends, hash-compatible with the deployed module)
  is installed from its repository instead; `bcrypt`, `cffi` and `pycparser`
  pinned for the Python 3.6 target.
