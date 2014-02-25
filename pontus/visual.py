from zope.interface import implements

from .interfaces import IVisualElement


class VisualElement(object):
    implements(IVisualElement)
    description = NotImplemented
    label = NotImplemented

    def __init__(self, description='', label=''):
        super(VisualElement, self).__init__()
        self.description = description
        self.label = label
