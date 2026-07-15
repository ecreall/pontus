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
