# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi
from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('pontus')


def includeme(config): # pragma: no cover
    config.include('.')
    config.scan('.')
    YEAR = 86400 * 365
    config.add_static_view('pontusstatic', 'pontus.dace_ui_extension:static', cache_max_age=YEAR)
