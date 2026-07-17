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


## 2026-07-16

- Phase 2 documentation of pontus, delivered in one pass (the layer is
  a quarter of dace's size): design document `architecture.md` (EN/FR —
  the behaviours-as-buttons principle, the merged result contract, the
  view lifecycle and behaviour binding, the POST round-trip through
  `ObjectData`, the composition algebra, index/navbar from the actions,
  oid-aware widgets, files/variants) and `usage-scenarios.md` (EN/FR —
  eight scenarios on the real API and the nova-ideo patterns).
- Full docstring pass from a complete read of the 3,600 lines:
  241 docstrings inserted with the AST tool (`tools/doc_coverage.py`
  added, same as dace). Coverage: 2.8 % → 88.3 % (18/18 modules,
  58/58 classes, 173/206 functions). The uncovered residue is the
  stated policy: constructors and a handful of trivial overrides.
  Notable knowledge fixed in writing: pontus's reading of
  `isautomatic` ("part of the object's index page"), the compositional
  `viewid`, the `Cancel` bypass, the per-button `<title>_failure`
  hooks, the `__viewid__`/`__contextsoids__` batch round-trip, and the
  wizard UI/behaviour transition conjunction.


## 2026-07-16 — Phase 3 / M2

- **pontus is green on Python 3.12: 8 tests, 0 failures, 0 errors**
  (the 7 historical tests plus the new regression test). Stack even
  more modern than the plan's target: deform 3.0.1 and colander 2.0
  (pulled by substanced 1.0b1), Chameleon 4.6 — the widget templates
  survived the diff pass without changes.
- The confirmed py2 remnant is repaired *with its test*, as the plan
  required: ``CallView.update`` subscripted ``dict.items()`` in its
  single-coordinate branch — unreachable on any Python 3 —
  ``test_CallView_single_coordinate`` now exercises it (two contexts,
  both children proven executed through ``request.viewexecuted``). The
  test uses fresh objects: substanced 1.0b1's ``add`` refuses parented
  re-adds, so the module-level singletons cannot be shared across
  tests any more.
- Traversal of the modern stack, each fix one line deep:
  ``pyramid.compat.map_`` → ``map``; ``deform.compat`` names shimmed;
  the ``'sortable'`` requirement re-registered (deform 3 dropped the
  key, still ships the script); the ``pyramid_mailer.testing`` include
  → direct ``DummyMailer`` utility (substanced now registers the
  mailer itself); ``tm.annotate_user = false`` — **note for M4**:
  pyramid_tm annotates the transaction user before traversal and
  substanced's groupfinder reads ``request.context``; every host on
  the modern stack needs this setting.
- Dual-stack packaging mirrored from M1: `constraints-modern.txt`,
  tox `py312`, CI `py312-tests` job (dace installed from git first),
  legacy job pinned to the `legacy-golden-master` tag. KuneAgi's
  buildout already pins pontus at the certified SHA.

- **T2 (first batch): the widget menagerie is pinned** — 11 tests in
  the functional harness (oids resolve through the objectmap, the
  deform renderer is app-wired). Coverage: widget.py **38 % → 75 %**;
  pontus total 63 % → 70 %; suite 19/19. Pinned contracts: the Select
  family resolves posted oid-strings to OBJECTS (other strings pass
  through; ``multiple=True`` is deform-3-mandatory for list pstructs;
  an empty list is ``null``); single RadioChoice takes the FIRST of a
  posted list; CheckboxChoice always answers a tuple; FileWidget
  collects its tmpstore on the root form and answers
  ``{'__objectoid__': oid}`` when only the reference was posted;
  ImageWidget's crop floats default to x/y 10.0, r 0.0, areas 100.0;
  SequenceWidget keeps parented subfields, and a widget-level child
  failure PROPAGATES as-is (no aggregation on this deform-3 path —
  ``sequence_fields`` keeps only the successes); ``Length`` raises
  half-interpolated messages ('$3'/'$5': str.format eats the braces of
  ``${min}`` and leaves the dollar); templates read ``field.widget.*``
  so serialize requires the canonical schema-widget wiring.

- **T2b: the Wizard machinery is pinned — and it hides TWO latent
  bugs, both immortalised.** `Wizard.update()` has never been able to
  run: with plain steps the session is never written (`init_stepid`
  belongs to the Form/MultipleView paths), so update walks the whole
  chain and dies on the final unconditional session `__delitem__`
  (KeyError); with a primed session, the resume branch reads
  `viewsinstances` — an attribute no code path ever creates — and
  raises AttributeError. The 51 % baseline agreed: those lines had
  never run anywhere. Everything around update is pinned green:
  graph construction (synthetic start/end, transition ids), the
  branch topology, `Transition.validate` conditions, the
  progression-bar math and its rendering, `get_view_requirements`
  following the session, and the `success` redirect (`mgmt_path`
  stubbed — a substanced request-method). 10 tests;
  view_operation.py **51 % → 68 %**; pontus total **75 %**;
  suite 29/29.
