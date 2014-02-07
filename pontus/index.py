# -*- coding: utf-8 -*-

from zope.component import getMultiAdapter
from zope.security.interfaces import Forbidden

from com.ecreall.omegsi.library.indexes import queryWorkItem
from grok import context, name
from omegsi.layout import Page

 


class EntityIndex(Page):

#    il faut voir avec les name et le context dans SD
#    name(u'index')
#    context(Ipropositiondaction)
     actions = []
#    actions = [Action1, Action2]

    def render(self, ):
        content = u'<div class="accordion" id="accordion">'
        for actionclass in actions:

            action = queryWorkItem(actionclass.processid, actionclass.id, self.request, self.context, actionclass.condition)
            if (not (action is None) ):
                view = getMultiAdapter((self.context, self.request), name= actionclass.view.name)
                view.update()
                # nous pouvons ajouter des balises pour délimiter les vues
                content = (content + view.content() )
        
        if (not content ):
            raise Forbidden
        
        return (content + '</div>' )





