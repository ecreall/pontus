# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

from pyramid.view import view_config

from dace.interfaces import IObject
from dace.util import getAllBusinessAction

from pontus.view import View, ViewError
from pontus.view_operation import MultipleView
from pontus.resources import (
    IndexViewErrorPrincipalmessage, IndexViewErrorCauses)
from pontus import _


@view_config(
    name='index',
    context=IObject,
    renderer='templates/views_templates/grid.pt',
    )
class Index(View):

    title = _('Index')
    viewid = 'index'

    def __init__(self,
                 context,
                 request,
                 parent=None,
                 wizard=None,
                 index=0,
                 **kwargs):
        View.__init__(self, context, request, parent, wizard, index, **kwargs)
        self.title = self.context.title

    def update(self):
        allactions = getAllBusinessAction(self.context, self.request, True)
        allactions.sort(key=lambda x: x.title)
        views = []
        for action in allactions:
            views.append(action.action_view)

        if views:
            indexmultiview = MultipleView(
                self.context, self.request, self.parent)
            indexmultiview.coordinates = self.coordinates
            indexmultiview._init_views(views)
            indexmultiview.before_update()
            return indexmultiview.update()

        error = ViewError()
        error.principalmessage = IndexViewErrorPrincipalmessage
        error.causes = IndexViewErrorCauses
        raise error
