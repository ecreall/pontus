# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi
"""Pontus — the presentation layer of the dace stack.

Turns dace business actions into deform forms and Pyramid views (one
submit button per behaviour), composes views through a merged result
contract, and renders the navigation an object offers. See
docs/en/architecture.md.
"""
import logging

from pyramid.i18n import TranslationStringFactory

log = logging.getLogger('pontus')

_ = TranslationStringFactory('pontus')


def includeme(config): # pragma: no cover
    """Pyramid inclusion: scan the package and mount the static assets."""
    config.include('.')
    config.scan('.')
    config.add_static_view('pontusstatic', 'pontus:static', cache_max_age=86400)
