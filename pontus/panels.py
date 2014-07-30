# -*- coding: utf8 -*-
from pyramid_layout.panel import panel_config
from pyramid.location import lineage
from pyramid.security import has_permission
from pyramid import renderers
from pyramid_layout.layout import Structure

from dace.objectofcollaboration.entity import Entity
from dace.objectofcollaboration.principal.util import has_any_roles


@panel_config(name='usermenu',
              renderer='templates/panels/usermenu.pt')
def usermenu_panel(context, request):
    return {}


@panel_config(name='breadcrumbs',
              renderer='templates/panels/breadcrumbs.pt')
class BreadcrumbsPanel(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def breadcrumbs(self):
        request = self.request
        context = self.context
        breadcrumbs = []
        for resource in lineage(context):
            
            if has_any_roles(roles=('Anonymous',), ignore_superiors=True):
                return {'breadcrumbs':[]}

            if isinstance(resource, Entity):
                url = request.resource_url(resource, '@@index')
            else:
                url = request.resource_url(resource)

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

    def render_group(self, name, group, active_items, isrelative):
        body = renderers.render('pontus:templates/panels/group.pt', 
                                {'name': name,
                                 'group':group,
                                 'active_items':active_items,
                                 'view': self,
                                 'isrelative':isrelative},
                                self.request)
        return Structure(body)

    def _classifier(self, actions, groups):
        actionsgroups = {}
        links = []
        titles = []
        for a in actions:
            if not a.action.groups and not(a.title in titles):
                titles.append(a.title)
                links.append(a)
                continue

            principalgroup_name = a.action.groups[0]
            principalgroup = None
            if principalgroup_name in actionsgroups:
                principalgroup = actionsgroups[principalgroup_name]
            else:
                principalgroup = actionsgroups[principalgroup_name] = {'links':[], 'subgroups':{}}

            if len(a.action.groups) == 1:
                if not(a.title in titles):
                    principalgroup['links'].append(a)
                    titles.append(a.title)

                continue

            lastgroup = None
            currentgroup = principalgroup
            for g in a.action.groups[1:]:
                if g in currentgroup['subgroups']:
                    lastgroup = currentgroup['subgroups'][g]
                else:
                    lastgroup = currentgroup['subgroups'][g] = {'links':[], 'subgroups':{}}

                currentgroup = lastgroup

            if not(a.title in titles):
                lastgroup['links'].append(a)
                titles.append(a.title)


        return actionsgroups, links


    def _actions(self):
        actions = [a for a in self.context.actions if not a.action.isautomatic and not a.action.access_controled]
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
        result['view'] = self
        return result


    def __call__(self):
       return self._actions()
