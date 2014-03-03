from zope.interface import implements

from .interfaces import IVisualisableElement


class VisualisableElement(object):
    implements(IVisualisableElement)
    description = ''
    label = ''

    def __init__(self, **kwargs):
        super(VisualisableElement, self).__init__()
        if kwargs.has_key('description'):
            self.description = kwargs.get('description')

        if kwargs.has_key('label'):
            self.label = kwargs.get('label')

