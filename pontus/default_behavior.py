# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

from pyramid.httpexceptions import HTTPFound

from dace.processinstance.core import  Behavior

from pontus import _


class Cancel(Behavior):

    behavior_id = "cancel"
    title = _("Cancel")
    description = ""

    def start(self, context, request, appstruct, **kw):
        behaviors_to_cancel = list(appstruct.get('behaviors', []))
        if self in  behaviors_to_cancel:
            behaviors_to_cancel.remove(self)

        for behavio in behaviors_to_cancel:
            behavio.cancel_execution(context, request, **kw)

        return {}

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))
