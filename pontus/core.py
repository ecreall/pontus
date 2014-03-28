# -*- coding: utf-8 -*-
import colander
import deform
from zope.interface import implements
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

    def init_stepid(self, schema, wizard=None):
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


class VisualisableElement(object):
    implements(IVisualisableElement)

    template = 'templates/visualisable_templates/object.pt'

    def __init__(self, **kwargs):
        super(VisualisableElement, self).__init__()
        self.title = ''
        self.label = ''
        self.description = ''
        if kwargs.has_key('description'):
            self.description = kwargs.get('description')

        if kwargs.has_key('label'):
            self.label = kwargs.get('label')

        if kwargs.has_key('title'):
            self.title = kwargs.get('title')

    def url(self, request, view=None, args=None):
        if view is None:
            return request.mgmt_path(self, '@@index')
        else:
            return request.mgmt_path(self, '@@'+view)

    def get_view(self, request, template=None):
        if template is None:
            template = self.template
        body = renderers.render(template, {'object':self}, request)

        return Structure(body)
