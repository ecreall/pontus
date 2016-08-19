.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide_addons.html
   This text does not appear on pypi or github. It is a comment.

==============
ecreall_pontus
==============

An application programming interface built upon the Pyramid web framework and substanced application. It provides libraries which make it easy to manage complex and imbricated views. For that purpose, Pontus introduces the concept of operations on views.

Examples
--------

This package is used in the following projects:

- `nova-ideo <https://github.com/ecreall/nova-ideo>`__
- `l'agenda commun <https://github.com/ecreall/lagendacommun>`__


Documentation
-------------

TODO


Translations
------------

This product has been translated into

- French


Installation
------------

Add `ecreall_pontus` in `install_requires` in your `setup.py`.
and edit `production.ini` in your Pyramid application to add::

    pyramid.includes =
        ...
        pontus


Contribute
----------

- Issue Tracker: https://github.com/ecreall/pontus/issues
- Source Code: https://github.com/ecreall/pontus


License
-------

The project is licensed under the AGPLv3+.
