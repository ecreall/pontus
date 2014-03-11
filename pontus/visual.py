from zope.interface import implements
from pyramid import renderers
from pyramid_layout.layout import Structure

from .interfaces import IVisualisableElement

class VisualisableElement(object):
    implements(IVisualisableElement)

    title = ''
    label = ''
    description = ''
    template = None

    def __init__(self, **kwargs):
        super(VisualisableElement, self).__init__()
        if kwargs.has_key('description'):
            self.description = kwargs.get('description')

        if kwargs.has_key('label'):
            self.label = kwargs.get('label')

        if kwargs.has_key('title'):
            self.title = kwargs.get('title')

        if self.template is None:
               self.template = 'templates/visualisable_templates/default.pt'

    def get_view(self, request, template=None):
        if template is None:
            template = self.template
        body = renderers.render(template, {'object':self}, request)

        return Structure(body)

