# -*- coding: utf8 -*-
from pyramid_layout.panel import panel_config
from pyramid.location import lineage
from pyramid.security import has_permission

from dace.objectofcollaboration.entity import Entity


@panel_config(name='usermenu',
              renderer='templates/panels/usermenu.pt')
def usermenu_panel(context, request):
    return {}


@panel_config(name='breadcrumbs',
              renderer='templates/panels/breadcrumbs.pt')
class Breadcrumbs_panel(object):


    def __init__(self, context, request):
        self.context = context
        self.request = request

    def breadcrumbs(self):
        request = self.request
        breadcrumbs = []
        for resource in lineage(request.context):
            if not has_permission('sdi.view', resource, request):
                return {'breadcrumbs':[]}
            
            url = request.sdiapi.mgmt_path(resource, '@@manage_main')
            if isinstance(resource, Entity):
                url = request.sdiapi.mgmt_path(resource, '@@index')
    
            name = getattr(resource, 'title', None)
            if name is None:
                name = resource.__name__ or 'Home'

            icon = request.registry.content.metadata(resource, 'icon')
            content_type = request.registry.content.typeof(resource)
            active = resource is request.context and 'active' or None
            bcinfo = {
                'url':url,
                'name':name,
                'active':active,
                'icon':icon,
                'content_type':content_type,
                }
            breadcrumbs.insert(0, bcinfo)
            if resource is request.virtual_root:
                break

        return {'breadcrumbs':breadcrumbs}

    def __call__(self):
       return self.breadcrumbs()


@panel_config(
    name = 'navbar',
    context = Entity ,
    renderer='templates/panels/navbar_view.pt'
    )
class NavBarPanel(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def _classifier(self, actions, groups):
        actionsgroups = {}
        titels = {}
        links = []
        for a in actions:
            if not a.action.groups:
                links.append(a)
                continue

            for g in groups:
                if g in a.action.groups:
                    if not(g in actionsgroups):
                        titels[g] = [a.title]
                        actionsgroups[g] = [a]
                    else:
                        if not(a.title in titels[g]):
                            actionsgroups[g].append(a)
                            titels[g].append(a.title)                

        for k, acs in dict(actionsgroups).iteritems():
            if len(acs) == 1:
                if not (acs[0] in links):
                    links.append(acs[0])

                actionsgroups.pop(k)
   
        return actionsgroups, links  

    def _actions(self):
        actions = self.context.actions
        view_name = self.request.view_name
        active_items = [a for a in actions if self.request.url.endswith(a.url)]
        groups = set()
        for a in actions:
            groups = groups.union(set(a.action.groups))

        startactions = [a for a in actions if a.action.isstart]
        activeactions = [a for a in actions if not a.action.isstart]
        result = {}
        sg, sl = self._classifier(startactions, groups)
        result['start']={'links': sl, 'groups': sg}
        g, l = self._classifier(activeactions, groups)
        result['active']={'links': l, 'groups': g}
        result['active_items'] = active_items
        return result


    def __call__(self):
       return self._actions()
