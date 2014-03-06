# -*- coding: utf8 -*-
from pyramid_layout.panel import panel_config


@panel_config(name='globalactions',
              renderer='templates/panels/globalactions.pt')
def globalactions_panel(context, request):
    return {}


@panel_config(name='breadcrumbs',
              renderer='templates/panels/breadcrumbs.pt')
def breadcrumbs_panel(context, request):
    return {}


@panel_config(name='usermenu',
              renderer='templates/panels/usermenu.pt')
def usermenu_panel(context, request):
    return {}
