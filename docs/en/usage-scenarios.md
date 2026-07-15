# Pontus — usage scenarios

*Companion to [`architecture.md`](architecture.md). The snippets follow the real API of the legacy code base and the patterns of nova-ideo, its reference host. French version: [`../fr/usage-scenarios.md`](../fr/usage-scenarios.md).*

## Scenario 1 — Wire Pontus into the application

```ini
pyramid.includes =
    substanced
    pyramid_layout
    dace
    pontus
```

`pontus.includeme` scans the package (views, panels, layout) and mounts the static assets (`pontusstatic`). Pontus assumes dace is present: views bind dace behaviours, panels read `context.actions`.

## Scenario 2 — A form whose buttons are business actions

The canonical pattern (nova-ideo's create/edit views all follow it):

```python
from pontus.form import FormView
from pontus.schema import select
from pontus.default_behavior import Cancel
from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS

class CreateIdeaView(FormView):
    title = _('Create an idea')
    name = 'createidea'
    schema = select(IdeaSchema(factory=Idea, editable=True),
                    ['title', 'text', 'keywords'])
    behaviors = [CreateIdea, Cancel]

DEFAULTMAPPING_ACTIONS_VIEWS.update({CreateIdea: CreateIdeaView})
```

Pontus instantiates `CreateIdea` (catalog discovery + the four dace guards — the view itself raises `ViewError` if no action validates), renders **one submit button per behaviour**, and on POST: `form.validate` → `ObjectData` builds the `Idea` (`appstruct['_object_data']`) → `CreateIdea.execute(context, request, appstruct)`. `Cancel` bypasses validation and unlocks. The last line registers the action→view mapping the index and navbar rely on.

## Scenario 3 — Add vs edit with `ObjectData`

The same schema serves both modes:

```python
schema = IdeaSchema(factory=Idea, editable=True, omit=('keywords',))
```

*Add*: no `__objectoid__` posted → `factory(**cleaned_values)`. *Edit*: the hidden `__objectoid__` resolves the object → `set_data(cleaned_values)`. Nodes flagged `to_omit`/`private` (csrf, ids, the `omit=` list) never reach the object. `FormView.default_data()` pre-fills the form — typically `return self.context.get_data(self.schema)`.

## Scenario 4 — Compose a page (`MultipleView`)

```python
from pontus.view_operation import MultipleView

class IdeaView(MultipleView):
    title = _('Idea')
    views = (SeeIdeaView, CommentsView, HistoryView)
```

Children validate independently (failed ones drop out), results merge slot by slot, one item stays *active* per slot — the tab pattern. Nested `(title, [views])` tuples build sub-groups. If a child is executable (a form) and finishes successfully, the multiple view short-circuits to its `success` (redirect).

## Scenario 5 — Batch operations over a selection

```python
from pontus.view_operation import CallSelectedContextsViews

class ModerateContents(CallSelectedContextsViews):
    title = _('Moderate')
    views = (PublishView, ArchiveView)          # one button each
    contexts = lambda self: find_entities(states=['submitted'])
```

The user checks contexts, picks an operation; pontus routes to `MergedFormsView` (form target: one merged form, one sub-entry per context, buttons suffixed *All*) or `CallView` (plain views, accordion), and dispatches each validated entry to the matching context's behaviour.

## Scenario 6 — A UI wizard mirroring a dace wizard

```python
class AddFileWizard(Wizard):
    views = {'choose': ChooseKindStep, 'upload': UploadStep,
             'meta': MetadataStep}
    transitions = (('choose', 'upload'),
                   ('choose', 'meta', True),            # default
                   ('upload', 'meta', False, has_file))  # condition
    behavior = AddFile
```

Steps are views; a transition validates only if the *behaviour's* wizard transition of the same id also does. The current step lives in the session; `include_informations = True` prepends a progression bar.

## Scenario 7 — Objects in select fields

```python
keywords = colander.SchemaNode(
    colander.Set(),
    widget=Select2Widget(values=..., multiple=True, create=True))
```

Pontus's select/checkbox/radio widgets serialize domain objects to oids and deserialize oids back to objects: the appstruct contains **real objects**. `AjaxSelect2Widget` fetches candidates lazily; unknown posted values survive round-trips (`title_getter`).

## Scenario 8 — Files and images

```python
picture = colander.SchemaNode(
    ObjectData(Image),
    widget=image_upload_widget,
    title=_('Picture'))
```

Upload creates a `pontus.file.Image` (dace object + substanced blob); `generate_variants` derives the `big/xlarge/large/medium/small/profil` thumbnails, each an attribute (`user.picture.profil.url`); the cropper posts the area of interest (`x`, `y`, `r`, `area_*`). `@@preview_image_upload` serves the temp-store preview before save.
