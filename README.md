# Pontus (`ecreall_pontus`)

Pontus is an application programming interface built upon the [Pyramid](https://trypyramid.com) web framework and the [substanced](https://github.com/Pylons/substanced) application. It provides libraries which make it easy to manage complex and imbricated views; for that purpose, Pontus introduces the concept of operations on views. It is the view and form layer used on top of the [DaCE](https://github.com/michaellaunay/dace) workflow engine.

## Repository status

This repository is a **maintained fork** of [`ecreall/pontus`](https://github.com/ecreall/pontus) (original development by Ecréall, 2014–2018), forked in July 2026 and maintained by Michaël Launay ([Logikascium](https://github.com/michaellaunay)). Ecréall's intellectual property was acquired by Logikascium in 2024; the license is unchanged: **AGPL v3+**.

This fork is part of the modernisation effort of the [Nova-Ideo](https://github.com/ecreall/nova-ideo) / [KuneAgi](https://github.com/ecreall/KuneAgi) participatory-innovation platform. The `master` branch is **dual-stack**: the library runs on the
certified legacy stack (tag `legacy-golden-master`) and on
**Python 3.12** (deform 3, colander 2, Chameleon 4 — phase 3 / M2).
The characterisation campaign brought the suite from 8 to **39 tests**
(coverage 63 % → 79 %) and uncovered **three latent bugs** in the
composition machinery — **all three fixed on 2026-07-17**, their
pinning tests flipped in conscience: see
[`docs/en/known-issues.md`](docs/en/known-issues.md), the
[roadmap](#roadmap--planned-updates) below and `CHANGES.md`.

## Features

- Operations on views, to compose complex and nested ("imbricated") views
- Form views and widgets built on deform (select2 widget, TinyMCE integration, …)
- Designed to render and execute the behaviours/actions of the [DaCE](https://github.com/michaellaunay/dace) workflow engine

## Current requirements (legacy)

- Python 3.6 — the modernisation targets Python 3.12
- `ecreall_dace` (use the maintained fork: [`michaellaunay/dace`](https://github.com/michaellaunay/dace)), `pyramid_layout`, substanced 1.0a1, Pillow
- Known-good dependency pins are provided in [`constraints-legacy.txt`](constraints-legacy.txt), extracted from the historical nova-ideo `versions.cfg` (the last environment in which the whole stack was known to work together)

## Installation

Add `ecreall_pontus` to `install_requires` in your `setup.py`, then edit `production.ini` in your Pyramid application:

```ini
pyramid.includes =
    ...
    pontus
```

For an isolated legacy development environment:

```bash
python3.6 -m pip install -c constraints-legacy.txt \
    "git+https://github.com/michaellaunay/dace.git#egg=ecreall_dace" \
    -e ".[test]"
```

## Running the tests

```bash
python setup.py test
```

A best-effort GitHub Actions workflow ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)) runs the suite inside a `python:3.6-buster` container, installing `ecreall_dace` from its maintained fork. It will be stabilised during Phase 1 of the roadmap (reproducible legacy build).

## Documentation

Documentation lives in [`docs/`](docs/):

- [`docs/en/`](docs/en/) — primary documentation, in English
- [`docs/fr/`](docs/fr/) — documentation in French

Audits, design documents and the worklog are maintained in both languages. See [`docs/README.md`](docs/README.md) for the documentation policy.

Design documents: [architecture](docs/en/architecture.md) · [usage scenarios](docs/en/usage-scenarios.md) (English originals; French mirrors under [`docs/fr/`](docs/fr/)).

## Used by

- [nova-ideo](https://github.com/ecreall/nova-ideo) and its variant [KuneAgi](https://github.com/ecreall/KuneAgi)
- [l'agenda commun](https://github.com/ecreall/lagendacommun)

## Roadmap — planned updates

The plan follows the Nova-Ideo modernisation audit (Logikascium, July 2026):

1. **Phase 1 — Reproducible legacy build ("golden master").** Frozen environment and green CI replaying the existing test suite: the non-regression baseline for everything below.
2. **Phase 2 — Exhaustive documentation.** Docstring pass over the whole package, documentation of the view/behaviour protocol shared with DaCE, glossary of the view-operation concepts.
3. **Phase 3 — Modernisation (target: version 2.0.0).** Ported **after** DaCE 2.0 (bottom-up dependency order):
   - Port to Python 3.12; Pyramid 2.x
   - deform 2.0.15 / colander 2 — goal: retire the historical deform fork
   - Move from the abandoned substanced 1.0a1 to the maintained, trimmed-down fork
   - Migrate tests to pytest (+ WebTest); packaging to PEP 621 (`pyproject.toml`) with `uv`; ruff linting; gradual typing
   - Python module names (dotted paths) are **frozen** to preserve existing ZODB pickles

Versioning: `1.1.x` = legacy maintenance on this fork; `2.0.0` = the modernised library.

## Translations

This product has been translated into: French.

## Contribute

- Issue tracker: <https://github.com/michaellaunay/pontus/issues>
- Source code: <https://github.com/michaellaunay/pontus>
- Historical upstream: <https://github.com/ecreall/pontus>

## License

The project is licensed under the AGPL v3 or later (AGPLv3+). See [`LICENSE`](LICENSE).
