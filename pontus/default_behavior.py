from pyramid.httpexceptions import HTTPFound

from dace.processinstance.core import  Behavior


class Cancel(Behavior):

    behavior_id = "cancel"
    title = "Cancel"
    description = ""

    def start(self, context, request, appstruct, **kw):
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))
