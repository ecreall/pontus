# Changelog

## Unreleased

### Fork maintenance — 2026-07-13 (`michaellaunay/pontus`)

- Repository forked from `ecreall/pontus`; maintenance resumed by Michaël Launay (Logikascium). Ecréall's intellectual property was acquired by Logikascium in 2024; license unchanged (AGPL v3+).
- `README.rst` and `CHANGES.rst` converted to Markdown (`README.md`, `CHANGES.md`); README rewritten with the repository status, legacy requirements and the modernisation roadmap.
- Build metadata updated: fork URLs, maintainer field, Markdown `long_description`, Python 3.6 classifier; minimal `pyproject.toml` added (PEP 518 `[build-system]` only — metadata stays in `setup.py` until the Phase 3 packaging migration); `MANIFEST.in` updated for Markdown files.
- Added `constraints-legacy.txt` (known-good 2017 dependency pins extracted from nova-ideo's `versions.cfg`) and a best-effort GitHub Actions workflow running the test suite in a `python:3.6-buster` container, with `ecreall_dace` installed from its maintained fork (to be stabilised in Phase 1).
- Bilingual documentation structure added (`docs/en/`, `docs/fr/`), including the worklog / fil de l'eau and the documentation policy (`docs/README.md`).

### Planned (modernisation roadmap → 2.0.0)

- Phase 1: reproducible legacy build + green CI (golden master).
- Phase 2: exhaustive documentation (docstrings, view/behaviour protocol shared with DaCE).
- Phase 3, after DaCE 2.0: Python 3.12, Pyramid 2.x; deform 2.0.15 / colander 2 (retire the historical deform fork); maintained substanced fork; pytest + WebTest; PEP 621 packaging with `uv`; ruff; gradual typing. Module dotted names frozen to preserve ZODB pickles.

### Inherited unreleased changes (upstream `1.1.1.dev`, 2017–2018)

- No entries were recorded upstream for this version; the repository nevertheless contains fixes committed until 2018-01-15 (last upstream commit: "fix behaviors order and viewid").

## 1.1.0 — 2017-02-25

- Refactoring of the select2 widget.

## 1.0.3 — 2017-01-06

- Add preventdelete tinymce plugin.
- Add url getter.

## 1.0.2 — 2016-09-15

- Fix style and translations.

## 1.0.1 — 2016-08-18

- Include mo files in the release.

## 1.0 — 2016-06-28

- Initial version.
