# -*- coding: utf-8 -*-
# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi

"""Base bricks: wizard steps and visualisable elements.

``VisualisableElement`` gives content classes their title/label/
description contract, their ``@@index`` URL and a rendered snippet
(``get_view``) — the mixin every nova-ideo content class carries.
"""
import colander
import deform
from zope.interface import implementer
from pyramid import renderers
from pyramid.threadlocal import get_current_request
from pyramid_layout.layout import Structure

from .interfaces import IVisualisableElement
from .schema import Schema
from pontus import _

STEPID = '__stepid__'

class Step(object):

    """Base of wizard steps: identity, wiring and completion state."""
    isexecutable = True

    def __init__(self, wizard=None, stepid=None):
        self.wizard = wizard
        self.stepid = stepid
        self.finished_successfully = False
        self._outgoing = []
        self._incoming = []

    def add_outgoing(self, transition):
        """Register an outgoing wizard transition."""
        self._outgoing.append(transition)

    def add_incoming(self, transition):
        """Register an incoming wizard transition."""
        self._incoming.append(transition)

    def init_stepid(self, schema=None, wizard=None):
        """Record this step as the current one in the session."""
        if self.wizard is not None:
            self.wizard.request.session[STEPID+self.wizard.viewid] = self.stepid
            #if self.id is not None:
            #    schema.add_idnode(STEPID+self.wizard.viewid, self.id)

            #if hasattr(self, 'parent'):
            #    self.parent.init_stepid(schema)


class VisualisableElementSchema(Schema):
    
    """The title/label/description schema slice."""
    title = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextInputWidget(),
        title=_('Title')
        )

    label = colander.SchemaNode(
        colander.String(),
        widget= deform.widget.TextInputWidget(),
        title=_('Label')
        )

    description = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextAreaWidget(rows=10, cols=60),
        title=_('Description')
        )


@implementer(IVisualisableElement)
class VisualisableElement(object):

    """Title/label/description contract of displayable contents."""
    template = 'templates/visualisable_templates/object.pt'

    def __init__(self, **kwargs):
        super(VisualisableElement, self).__init__(**kwargs)
        self.title = kwargs.get('title', '')
        self.label = kwargs.get('label', '')
        self.description = kwargs.get('description', '')

    @property
    def url(self,):
        """The object's ``@@index`` URL (current request)."""
        request = get_current_request()
        return request.resource_url(self, '@@index')

    def get_url(self, request):
        """The object's ``@@index`` URL for ``request``."""
        return request.resource_url(self, '@@index')

    def get_view(self, request, template=None):
        """Render the object snippet (``template``) as a layout Structure."""
        if template is None:
            template = self.template
        body = renderers.render(template, {'object': self}, request)

        return Structure(body)
