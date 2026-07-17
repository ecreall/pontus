# Problèmes connus — RÉSOLUS (mémoire historique)

*Découverts pendant la campagne de caractérisation de juillet 2026
et **RÉSOLUS le 17/07/2026** : les trois correctifs ont atterri
ensemble et leurs tests d'épinglage ont été retournés en conscience —
chacun garde désormais la réparation
(`test_update_walks_the_chain_to_success`,
`test_update_primed_resumes_and_completes`,
`test_button_post_valid_selection`,
`test_construction_leaves_the_operation_classes_untouched`). Les
chaînes causales ci-dessous sont conservées comme mémoire historique.
Version anglaise : [`../en/known-issues.md`](../en/known-issues.md).*

## 1. `Wizard.update()` ne peut pas tourner (deux modes d'échec)

`pontus.view_operation.Wizard` construit correctement son graphe
d'étapes (topologie, start/end synthétiques, transitions, barre de
progression — tout est épinglé vert), mais `update()` n'a jamais pu
aboutir :

- **Session non amorcée** (steps `BasicView` simples) : les steps
  n'écrivent jamais la clé de session (`Step.init_stepid` n'est
  appelé que sur les chemins Form/MultipleView), donc update parcourt
  toute la chaîne avec succès et meurt sur le `session.__delitem__`
  FINAL et inconditionnel → `KeyError`.
  Épinglé par `test_update_unprimed_dies_on_final_cleanup`.
- **Session amorcée** : la branche de reprise lit
  `self.viewsinstances`, attribut qu'aucun chemin de code ne crée (le
  constructeur bâtit `nodes`) → `AttributeError`.
  Épinglé par `test_update_primed_resume_is_broken`.

Les wizards de production passent donc par une autre machinerie (le
côté behaviors de dace), jamais par cette méthode.

## 2. `CallSelectedContextsViews` : la sélection directe par bouton meurt

Une sélection VALIDE postée par les boutons du formulaire atteint
`validated['items'].values()` — mais le `colander.Set` moderne
déserialise en **set** (la bibliothèque d'époque répondait
vraisemblablement un dict) → `AttributeError: 'set' object has no
attribute 'values'`. Le chemin de sélection directe n'a jamais abouti
sur cette pile ; **seul le round-trip `__viewid__` fonctionne**
(épinglé de bout en bout : le behavior cible s'exécute une fois par
contexte sélectionné).
Épinglé par `test_button_post_valid_selection_hits_the_set_bug`.

Fragilité voisine, épinglée aussi : un payload `__contextsoids__` vide
lève `ViewError`, mais un `':'` seul meurt plus tôt sur `int('')`
(`ValueError`).

## 3. Design smell : mutation de classe dans `_init_children`

`CallSelectedContextsViews._init_children` écrase
`CallView.title`/`views` et `MergedFormsView.title`/`views` **au
niveau classe** — effet de bord global entre instances. La suite de
tests restaure les originaux en `tearDown` ; une correction devrait
en faire des attributs d'instance.
Épinglé par `test_construction_mutates_the_operation_classes`.
