# Fil de l'eau

Journal au fil de l'eau des travaux sur ce dépôt, du plus récent au plus ancien.
English version: [`../en/worklog.md`](../en/worklog.md).

## 2026-07-13

- Fork de `ecreall/pontus` vers `michaellaunay/pontus` ; reprise de la
  maintenance par Michaël Launay (Logikascium).
- Conversion de `README.rst` et `CHANGES.rst` en Markdown ; README réécrit avec
  le statut du dépôt et la feuille de route de modernisation.
- Mise à jour des métadonnées de build (`setup.py` : URLs du fork, champ
  mainteneur, description longue en Markdown, classifieur Python 3.6) ; ajout
  d'un `pyproject.toml` minimal (PEP 518) ; mise à jour du `MANIFEST.in`.
- Ajout de `constraints-legacy.txt` (épinglages de dépendances 2017 connus pour
  fonctionner) et d'un workflow de CI legacy best-effort (`python:3.6-buster`,
  `ecreall_dace` installé depuis son fork maintenu).
- Mise en place de la structure de documentation bilingue (`docs/en`,
  `docs/fr`) et de ce fil de l'eau.
- Application préventive, avant même le premier run de pontus, des correctifs
  d'époque appris des deux premiers runs de dace : `setuptools<46` (les sdists
  de 2016/2017 utilisent l'API `Feature` supprimée dans setuptools 46), apt
  repointé vers archive.debian.org (buster archivée en 2024), `libzmq3-dev`
  (pyzmq 14.4.1, via ecreall_dace, n'a pas de wheel Python 3.6),
  `actions/checkout` passé en v5, et `mock` embarqué dans l'extra `[test]`
  (le scan venusian de substanced importe ses propres modules de test à la
  création du Configurator).
- Ajout de `libjpeg-dev` et `zlib1g-dev` : Pillow 3.4.2 est antérieur aux
  wheels Python 3.6 (vérifié sur PyPI) et doit être compilé depuis les
  sources.


## 2026-07-14

- Suppression de la dependance C amont `cryptacular` de l'environnement de
  CI (elle n'etait pas epinglee : pip compilait silencieusement le sdist
  1.6.2). La reecriture drop-in maintenue (`michaellaunay/cryptacular` 2.x,
  backends bcrypt PyCA + hashlib, compatible hash pour hash avec le module
  deploye) est installee depuis son depot a la place ; `bcrypt`, `cffi` et
  `pycparser` epingles pour la cible Python 3.6.


## 2026-07-16

- Documentation de phase 2 de pontus, livrée en une passe (la couche
  fait le quart de dace) : document de conception `architecture.md`
  (EN/FR — le principe behaviors-comme-boutons, le contrat de résultat
  fusionné, le cycle de vie des vues et la liaison aux behaviors,
  l'aller-retour du POST via `ObjectData`, l'algèbre de composition,
  index/navbar depuis les actions, widgets conscients des oids,
  fichiers/variantes) et `usage-scenarios.md` (EN/FR — huit scénarios
  sur l'API réelle et les motifs de nova-ideo).
- Passe de docstrings complète après lecture intégrale des
  3 600 lignes : 241 docstrings insérés avec l'outil AST
  (`tools/doc_coverage.py` ajouté, comme pour dace). Couverture :
  2,8 % → 88,3 % (18/18 modules, 58/58 classes, 173/206 fonctions). Le
  résidu non couvert relève de la politique annoncée : constructeurs et
  quelques surcharges triviales. Savoirs notables fixés par écrit : la
  lecture pontus d'`isautomatic` (« fait partie de la page d'index de
  l'objet »), le `viewid` compositionnel, le court-circuit `Cancel`,
  les hooks d'échec `<titre>_failure` par bouton, l'aller-retour de lot
  `__viewid__`/`__contextsoids__`, et la conjonction des transitions
  wizard interface/behavior.


## 16/07/2026 — Phase 3 / M2

- **pontus est vert sur Python 3.12 : 8 tests, 0 échec, 0 erreur**
  (les 7 tests historiques plus le nouveau test de régression). Pile
  encore plus moderne que la cible du plan : deform 3.0.1 et
  colander 2.0 (tirés par substanced 1.0b1), Chameleon 4.6 — les
  templates de widgets ont survécu à la passe de diff sans
  modification.
- Le reliquat py2 confirmé est réparé *avec son test*, comme le plan
  l'exigeait : ``CallView.update`` indexait ``dict.items()`` dans sa
  branche à coordonnée unique — inatteignable sur tout Python 3 —
  ``test_CallView_single_coordinate`` l'exerce désormais (deux
  contextes, exécution des deux enfants prouvée par
  ``request.viewexecuted``). Le test emploie des objets frais : le
  ``add`` de substanced 1.0b1 refuse le ré-ajout d'objets parentés,
  les singletons de module ne peuvent plus être partagés entre tests.
- Traversée de la pile moderne, chaque correction à une ligne de
  fond : ``pyramid.compat.map_`` → ``map`` ; noms de
  ``deform.compat`` shimés ; l'exigence ``'sortable'`` réenregistrée
  (deform 3 a retiré la clé, livre toujours le script) ; l'include
  ``pyramid_mailer.testing`` → utilitaire ``DummyMailer`` direct
  (substanced enregistre désormais le mailer lui-même) ;
  ``tm.annotate_user = false`` — **note pour M4** : pyramid_tm annote
  l'utilisateur de la transaction avant la traversée et le groupfinder
  de substanced lit ``request.context`` ; tout hôte de la pile moderne
  a besoin de ce réglage.
- Emballage bi-pile calqué sur M1 : `constraints-modern.txt`, tox
  `py312`, job CI `py312-tests` (dace installé depuis git d'abord),
  job legacy épinglé sur le tag `legacy-golden-master`. Le buildout de
  KuneAgi épingle déjà pontus au SHA certifié.

- **T2 (premier lot) : la ménagerie de widgets est épinglée** — 11
  tests dans le harnais fonctionnel (les oids se résolvent par
  l'objectmap, le renderer deform est câblé par l'app). Couverture :
  widget.py **38 % → 75 %** ; total pontus 63 % → 70 % ; suite 19/19.
  Contrats épinglés : la famille Select résout les oid-chaînes postées
  en OBJETS (les autres chaînes passent ; ``multiple=True`` est
  obligatoire en deform 3 pour les listes ; liste vide → ``null``) ;
  RadioChoice simple prend le PREMIER d'une liste postée ;
  CheckboxChoice répond toujours un tuple ; FileWidget collecte son
  tmpstore sur le formulaire racine et répond
  ``{'__objectoid__': oid}`` quand seule la référence est postée ;
  les flottants de recadrage d'ImageWidget ont pour défauts x/y 10.0,
  r 0.0, aires 100.0 ; SequenceWidget conserve les sous-champs
  parentés, et une faute de niveau widget chez un enfant SE PROPAGE
  telle quelle (pas d'agrégation sur ce chemin deform 3 —
  ``sequence_fields`` ne garde que les succès) ; ``Length`` lève des
  messages semi-interpolés ('$3'/'$5' : str.format mange les
  accolades de ``${min}`` et laisse le dollar) ; les templates lisent
  ``field.widget.*`` donc serialize exige le câblage canonique
  widget-sur-schéma.

- **T2b : la machinerie du Wizard est épinglée — et elle cache DEUX
  bugs latents, immortalisés tous deux.** `Wizard.update()` n'a jamais
  pu tourner : avec des steps simples la session n'est jamais écrite
  (`init_stepid` appartient aux chemins Form/MultipleView), donc
  update parcourt toute la chaîne et meurt sur le `__delitem__` de
  session final et inconditionnel (KeyError) ; session amorcée, la
  branche de reprise lit `viewsinstances` — attribut qu'aucun chemin
  de code ne crée — et lève AttributeError. La base à 51 % en
  témoignait : ces lignes n'avaient jamais tourné nulle part. Tout ce
  qui entoure update est épinglé vert : construction du graphe
  (start/end synthétiques, ids de transitions), topologie branchée,
  conditions de `Transition.validate`, calcul de la barre de
  progression et son rendu, `get_view_requirements` suivant la
  session, et la redirection `success` (`mgmt_path` stubé —
  méthode-requête substanced). 10 tests ; view_operation.py
  **51 % → 68 %** ; total pontus **75 %** ; suite 29/29.

- **T2c : le patron batch `CallSelectedContextsViews` est épinglé — et
  le bug latent n°3 rejoint la collection.** Une sélection VALIDE par
  bouton meurt sur `validated['items'].values()` : le `colander.Set`
  moderne déserialise en set (la bibliothèque d'époque répondait
  vraisemblablement un dict) — le chemin de sélection directe n'a donc
  jamais pu aboutir sur cette pile ; seul le round-trip `__viewid__`
  vit, et il est épinglé de bout en bout (le behavior cible s'exécute
  une fois par contexte sélectionné, le payload vide lève `ViewError`,
  et l'analyse fragile de `':'` meurt sur `int('')`). Épinglés aussi :
  le routage de construction (CallView vs MergedFormsView par
  `IFormView`, clés soulignées, nommage des boutons deform), le
  protocole contexts()-est-appelé, la mutation de titre AU NIVEAU
  CLASSE des opérations partagées (design smell — restaurée en
  tearDown), le rendu du formulaire de sélection (snippets Structure,
  échappés sinon), et la branche d'échec de validation (drapeau
  `isactive`). 10 tests ; view_operation.py **68 % → 79 %** ; total
  pontus **79 %** (63 % au départ de la campagne) ; suite 39/39.

- **Rafraîchissement documentaire.** Le README énonce la réalité
  bi-pile et les chiffres de campagne ; CHANGES consolide T2/T2b/T2c ;
  les trois bugs latents reçoivent leur `known-issues.md` bilingue
  (chaînes causales et tests à retourner par toute correction) ;
  l'architecture pointe dessus.

- **Les trois bugs latents sont réparés, leurs tests retournés en
  conscience.** Wizard.update tourne sur ses deux chemins (reprise via
  `self.nodes`, `session.pop` final tolérant) ; la sélection validée
  par bouton se consomme en set ou en mapping (le chemin direct
  aboutit sur les deux piles) ; `_init_children` bâtit des
  sous-classes par cible (plus de mutation des classes partagées).
  Suite 39/39 ; known-issues.md devient la mémoire historique.

- **Fenêtre des renommages.** Les constantes de messages `Mutltiple*`
  deviennent `Multiple*` (chaînes de module — rien de persisté) ; des
  alias de compatibilité gardent les noms historiques importables.
