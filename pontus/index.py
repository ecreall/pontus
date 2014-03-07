from pyramid.threadlocal import get_current_registry
from pyramid import renderers

from substanced.sdi import mgmt_view

from dace.interfaces import IBusinessAction, IProcessDefinition, IObject
from dace.util import find_catalog
from pontus.view import View

#a changer...
def comp(action1, action2):
    if action1.title < action2.title:
        return -1
    elif action1.title > action2.title:
        return 1
  
    return 0


@mgmt_view(
    name='index',
    tab_title='Voir',
    context=IObject,
    renderer='templates/view.pt',
    )
class Index(View):

    title = 'Voire'
    viewid = 'index'

    def update(self):
        dace_catalog = find_catalog('dace')
        context_id_index = dace_catalog['context_id']
        object_provides_index = dace_catalog['object_provides']
        isautomatic_index = dace_catalog['isautomatic']
        query = object_provides_index.any((IBusinessAction.__identifier__,)) & \
                context_id_index.any(self.context.__provides__.declared) & \
                isautomatic_index.eq(True)
        results = query.execute().all()
        allactions = [action for action in results if action.validate(context)]
        registry = get_current_registry()
        allprocess = registry.getUtilitiesFor(IProcessDefinition)
        # Add start actions
        for name, pd in allprocess:
            if not pd.isControlled and (not pd.isUnique or (pd.isUnique and not pd.isInstantiated)):
                wis = pd.createStartWorkItem(None)
                for key in wis.keys():
                    swisactions = wis[key].actions
                    for action in swisactions:
                        if action.isautomatic and action.validate(self.context) :
                            allactions.append(action)

        allactions.sort(cmp=comp)
        views = []
        for action in allactions:
            views.append(action.view_action)

        if views:
            indexmultiview = MultipleView(self.context, self.request)
            self._buildMultiViewTree(views)
            return indexmultiview.update()
        
        warning_message = renderers.render('templates/forbidden.pt', {}, self.request)
        item =self.adapt_item('', self.viewid)
        item['messages'] = {'warning': [warning_message]}
        result = {'js_links': [], 'css_links': [], 'slots': {self.slot:[item]}}
        return result


