# Pontus — scénarios d'utilisation

*Compagnon de [`architecture.md`](architecture.md). Les extraits suivent l'API réelle de la base legacy et les motifs de nova-ideo, son hôte de référence. English version: [`../en/usage-scenarios.md`](../en/usage-scenarios.md).*

## Scénario 1 — Câbler Pontus dans l'application

```ini
pyramid.includes =
    substanced
    pyramid_layout
    dace
    pontus
```

`pontus.includeme` scanne le paquet (vues, panels, layout) et monte les ressources statiques (`pontusstatic`). Pontus suppose dace présent : les vues lient des behaviors dace, les panels lisent `context.actions`.

## Scénario 2 — Un formulaire dont les boutons sont des actions métier

Le motif canonique (toutes les vues de création/édition de nova-ideo le suivent) :

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

Pontus instancie `CreateIdea` (découverte par catalogue + les quatre gardes dace — la vue elle-même lève `ViewError` si aucune action ne valide), rend **un bouton de soumission par behavior**, et au POST : `form.validate` → `ObjectData` construit l'`Idea` (`appstruct['_object_data']`) → `CreateIdea.execute(context, request, appstruct)`. `Cancel` court-circuite la validation et déverrouille. La dernière ligne enregistre le mapping action→vue sur lequel index et navbar s'appuient.

## Scénario 3 — Ajout vs édition avec `ObjectData`

Le même schéma sert aux deux modes :

```python
schema = IdeaSchema(factory=Idea, editable=True, omit=('keywords',))
```

*Ajout* : pas de `__objectoid__` posté → `factory(**valeurs_nettoyées)`. *Édition* : le `__objectoid__` caché résout l'objet → `set_data(valeurs_nettoyées)`. Les nœuds marqués `to_omit`/`private` (csrf, ids, la liste `omit=`) n'atteignent jamais l'objet. `FormView.default_data()` préremplit le formulaire — typiquement `return self.context.get_data(self.schema)`.

## Scénario 4 — Composer une page (`MultipleView`)

```python
from pontus.view_operation import MultipleView

class IdeaView(MultipleView):
    title = _('Idea')
    views = (SeeIdeaView, CommentsView, HistoryView)
```

Les enfants se valident indépendamment (les refusés sortent), les résultats fusionnent emplacement par emplacement, un item reste *actif* par emplacement — le motif des onglets. Les tuples imbriqués `(titre, [vues])` construisent des sous-groupes. Si un enfant exécutable (un formulaire) s'achève avec succès, la vue multiple court-circuite vers son `success` (redirection).

## Scénario 5 — Opérations par lot sur une sélection

```python
from pontus.view_operation import CallSelectedContextsViews

class ModerateContents(CallSelectedContextsViews):
    title = _('Moderate')
    views = (PublishView, ArchiveView)          # un bouton chacune
    contexts = lambda self: find_entities(states=['submitted'])
```

L'utilisateur coche des contextes, choisit une opération ; pontus route vers `MergedFormsView` (cible formulaire : un formulaire fusionné, une sous-entrée par contexte, boutons suffixés *All*) ou `CallView` (vues simples, accordéon), et distribue chaque entrée validée au behavior du contexte correspondant.

## Scénario 6 — Un wizard d'interface miroir d'un wizard dace

```python
class AddFileWizard(Wizard):
    views = {'choose': ChooseKindStep, 'upload': UploadStep,
             'meta': MetadataStep}
    transitions = (('choose', 'upload'),
                   ('choose', 'meta', True),            # défaut
                   ('upload', 'meta', False, has_file))  # condition
    behavior = AddFile
```

Les étapes sont des vues ; une transition ne se valide que si la transition du wizard *du behavior* de même id se valide aussi. L'étape courante vit en session ; `include_informations = True` préfixe une barre de progression.

## Scénario 7 — Des objets dans les champs de sélection

```python
keywords = colander.SchemaNode(
    colander.Set(),
    widget=Select2Widget(values=..., multiple=True, create=True))
```

Les widgets select/checkbox/radio de pontus sérialisent les objets du domaine en oids et désérialisent les oids en objets : l'appstruct contient de **vrais objets**. `AjaxSelect2Widget` va chercher les candidats paresseusement ; les valeurs postées inconnues survivent aux allers-retours (`title_getter`).

## Scénario 8 — Fichiers et images

```python
picture = colander.SchemaNode(
    ObjectData(Image),
    widget=image_upload_widget,
    title=_('Picture'))
```

L'upload crée une `pontus.file.Image` (objet dace + blob substanced) ; `generate_variants` dérive les vignettes `big/xlarge/large/medium/small/profil`, chacune un attribut (`user.picture.profil.url`) ; le cropper poste la zone d'intérêt (`x`, `y`, `r`, `area_*`). `@@preview_image_upload` sert la prévisualisation du temp-store avant sauvegarde.
