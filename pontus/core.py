# -*- coding: utf-8 -*-
# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

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

    isexecutable = True

    def __init__(self, wizard=None, stepid=None):
        self.wizard = wizard
        self.stepid = stepid
        self.finished_successfully = False
        self._outgoing = []
        self._incoming = []

    def add_outgoing(self, transition):
        self._outgoing.append(transition)

    def add_incoming(self, transition):
        self._incoming.append(transition)

    def init_stepid(self, schema=None, wizard=None):
        if self.wizard is not None:
            self.wizard.request.session[STEPID+self.wizard.viewid] = self.stepid
            #if self.id is not None:
            #    schema.add_idnode(STEPID+self.wizard.viewid, self.id)

            #if hasattr(self, 'parent'):
            #    self.parent.init_stepid(schema)


class VisualisableElementSchema(Schema):
    
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

    template = 'templates/visualisable_templates/object.pt'

    def __init__(self, **kwargs):
        super(VisualisableElement, self).__init__(**kwargs)
        self.title = ''
        self.label = ''
        self.description = ''
        if 'description' in kwargs:
            self.description = kwargs.get('description')

        if 'label' in kwargs:
            self.label = kwargs.get('label')

        if 'title' in kwargs:
            self.title = kwargs.get('title')

    @property
    def url(self,):
        request = get_current_request()
        return request.resource_url(self, '@@index')

    def get_view(self, request, template=None):
        if template is None:
            template = self.template
        body = renderers.render(template, {'object':self}, request)

        return Structure(body)
