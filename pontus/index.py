import functools
from pyramid.threadlocal import get_current_registry
from pyramid.view import view_config
import venusian
from substanced.sdi import mgmt_view
from pyramid.util import action_method
from pontus.view import View
from dace.interfaces import IBusinessAction, IProcessDefinition, IObject
from dace.util import find_catalog
from substanced.util import _
from pontus.util import get_view

#a changer...
def comp(action1, action2):
    if action1.title < action2.title:
        return -1
    elif action1.title > action2.title:
        return 1
  
    return 0

@view_config(name='index', context=IObject, renderer='templates/view.pt')
@mgmt_view(
    name='index',
    tab_title='Voir',
    context=IObject,
    renderer='templates/view.pt',
    )
class Index(View):

    title = 'Voire'

    def __call__(self):
        #red = render_view(self.context, self.request, name='index')
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
        # Add start workitem
        for name, pd in allprocess:
            if not pd.isControlled and (not pd.isUnique or (pd.isUnique and not pd.isInstantiated)):
                wis = pd.createStartWorkItem(None)
                for key in wis.keys():
                    swisactions = wis[key].actions
                    for action in swisactions:
                        if action.isautomatic and action.validate(self.context) :
                            allactions.append(action)

        allactions.sort(cmp=comp)
        content = u'<div class="accordion" id="accordion">'
        for action in allactions:
            view = get_view(self.context, self.request, name=action.view_name)
            response = view(self.context, self.request)
            #self.request.mgmt_path(self.context, '@@'+action.view_name)
            # nous pouvons ajouter des balises pour les vues
            content += response.rbody
        
        if (not content ):
            raise Forbidden

        result = {'content':(content + '</div>' ) }
        return result


