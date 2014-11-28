# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi
# -*- coding: utf8 -*-
from pyramid_layout.layout import layout_config


@layout_config(template='templates/master.pt')
class GlobalLayout(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
