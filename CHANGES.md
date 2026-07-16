# Changelog

## Unreleased

### Phase 3 / M2 — 2026-07-16 (Python 3.12)

- Python 3.12 support on the modern stack (dace 2.0.0.dev0, substanced
  1.0b1, deform 3.0.1, colander 2.0, Chameleon 4.6) — 8/8 tests green;
  see `constraints-modern.txt`. Version bumped to 2.0.0.dev0.
- The unreachable py2 branch of ``CallView.update`` (it subscripted
  ``dict.items()``, crashing on any Python 3) is repaired and covered
  by a new regression test, ``test_CallView_single_coordinate``.
- deform 3 compatibility: local shims for the removed ``deform.compat``
  names; the historical ``'sortable'`` widget requirement re-registered
  onto the script deform still ships.
- Modern-stack compatibility: ``pyramid.compat.map_`` shim; the
  ``pyramid_mailer.testing`` include (which now conflicts with
  substanced's own mailer registration) replaced by registering the
  ``DummyMailer`` utility directly; ``tm.annotate_user = false`` in the
  harness — pyramid_tm reads ``authenticated_userid`` before traversal
  and substanced 1.0b1's groupfinder needs ``request.context`` (hosts
  on the modern stack need the same setting).
- Python 3.6 support moves to the ``legacy-golden-master`` tag,
  consumed by the pinned KuneAgi golden master and the legacy CI job.


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
