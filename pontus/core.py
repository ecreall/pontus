# -*- coding: utf-8 -*-
import colander
import deform
from zope.interface import implementer
from pyramid import renderers
from pyramid_layout.layout import Structure

from .interfaces import IVisualisableElement
from .schema import Schema

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
        widget=deform.widget.TextInputWidget()
        )

    label = colander.SchemaNode(
        colander.String(),
        widget= deform.widget.TextInputWidget()
        )

    description = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextAreaWidget(rows=10, cols=60)
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

    def url(self, request, view=None, args=None):
        if view is None:
            return request.resource_url(self, '@@index')
        else:
            return request.resource_url(self, '@@'+view)

    def get_view(self, request, template=None):
        if template is None:
            template = self.template
        body = renderers.render(template, {'object':self}, request)

        return Structure(body)
