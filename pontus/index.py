from substanced.sdi import mgmt_view

from dace.interfaces import IObject
from dace.util import getAllBusinessAction
from pontus.view import View, ViewError
from pontus.view_operation import MultipleView
from pontus.resources import IndexViewErrorPrincipalmessage, IndexViewErrorCauses


@mgmt_view(
    name='index',
    tab_title='Voir',
    context=IObject,
    renderer='templates/view.pt',
    )
class Index(View):

    title = 'Voir'
    viewid = 'index'

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        View.__init__(self, context, request, parent, wizard, index,**kwargs)
        self.title = self.context.title

    def update(self):
        allactions = getAllBusinessAction(self.context, self.request, True)
        allactions.sort(key=lambda x: x.title)
        views = []
        for action in allactions:
            views.append(action.action_view)

        if views:
            indexmultiview = MultipleView(self.context, self.request, self.parent)
            indexmultiview.coordinates = self.coordinates
            indexmultiview._init_views(views)
            indexmultiview.before_update()
            return indexmultiview.update()

        e = ViewError()
        e.principalmessage = IndexViewErrorPrincipalmessage
        e.causes = IndexViewErrorCauses
        raise e
