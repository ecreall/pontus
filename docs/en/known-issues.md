# Known issues (pinned by the test suite)

*Discovered during the 2026-07 characterisation campaign. Each issue
is immortalised by a test that passes TODAY by asserting the broken
behaviour — any fix must flip that test consciously. French version:
[`../fr/known-issues.md`](../fr/known-issues.md).*

## 1. `Wizard.update()` cannot run (two failure modes)

`pontus.view_operation.Wizard` builds its step graph correctly
(topology, synthetic start/end, transitions, progression bar — all
pinned green), but `update()` has never been able to complete:

- **Unprimed session** (plain `BasicView` steps): the steps never
  write the session key (`Step.init_stepid` is only called on the
  Form/MultipleView paths), so update walks the whole chain
  successfully and dies on the FINAL unconditional
  `session.__delitem__` → `KeyError`.
  Pinned by `test_update_unprimed_dies_on_final_cleanup`.
- **Primed session**: the resume branch reads `self.viewsinstances`,
  an attribute no code path ever creates (the constructor builds
  `nodes`) → `AttributeError`.
  Pinned by `test_update_primed_resume_is_broken`.

Production wizards therefore run through other machinery (the dace
behaviour side), never through this method.

## 2. `CallSelectedContextsViews`: direct button selection dies

A VALID selection posted through the form buttons reaches
`validated['items'].values()` — but modern `colander.Set`
deserializes to a **set** (the era library plausibly answered a
dict) → `AttributeError: 'set' object has no attribute 'values'`.
The direct-selection path has never completed on this stack; **only
the `__viewid__` round-trip works** (pinned end to end: the target
behaviour executes once per selected context).
Pinned by `test_button_post_valid_selection_hits_the_set_bug`.

Related brittleness, also pinned: an empty `__contextsoids__` payload
raises `ViewError`, but a lone `':'` dies earlier on `int('')`
(`ValueError`).

## 3. Design smell: class-level mutation in `_init_children`

`CallSelectedContextsViews._init_children` overwrites
`CallView.title`/`views` and `MergedFormsView.title`/`views` **at
class level** — a global side effect across instances. The test suite
restores the originals in `tearDown`; a fix should move these to
instance attributes.
Pinned by `test_construction_mutates_the_operation_classes`.
