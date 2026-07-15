# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi

"""The universal Cancel behaviour of forms."""
from pyramid.httpexceptions import HTTPFound

from dace.processinstance.core import  Behavior

from pontus import _


class Cancel(Behavior):

    """Form-level cancel: bypasses validation, runs ``cancel_execution`` on
    the sibling behaviours (dace unlocking) and redirects to the index.
    """
    behavior_id = "cancel"
    title = _("Cancel")
    description = ""

    def start(self, context, request, appstruct, **kw):
        """Cancel every other behaviour posted with the form."""
        behaviors_to_cancel = list(appstruct.get('behaviors', []))
        if self in  behaviors_to_cancel:
            behaviors_to_cancel.remove(self)

        for behavio in behaviors_to_cancel:
            behavio.cancel_execution(context, request, **kw)

        return {}

    def redirect(self, context, request, **kw):
        """Back to the context's ``@@index``."""
        return HTTPFound(request.resource_url(context, "@@index"))
