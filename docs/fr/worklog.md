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
