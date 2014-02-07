# -*- coding: utf-8 -*-

from zope.component import getMultiAdapter
from zope.security.interfaces import Forbidden

from com.ecreall.omegsi.library.indexes import queryWorkItem
from grok import context, name
from omegsi.layout import Page

 


class BaseIndex(Page):

#    il faut voir avec le name et le context dans SD
#    name(u'index')
#    context(Ipropositiondaction)
     actions = []


    def render(self, ):
        content = u'<div class="accordion" id="accordion">'
        for actionclass in actions:

            action = queryWorkItem(actionclass.process_id, actionclass.node_id, self.request, self.context) # actionclass.condition: est vérifier par le validate() de l'action
            if (not (action is None) ):
                view = getMultiAdapter((self.context, self.request), name=actionclass.view_name)
                view.update()
                # nous pouvons ajouter des balises pour délimiter les vues
                content += view.content()
        
        if (not content ):
            raise Forbidden
        
        return (content + '</div>' )



# exemple

#class MonIndex(BaseIndex):
#
#    actions = [Action1, Action2]



