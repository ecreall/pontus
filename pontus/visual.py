from zope.interface import implements

from .interfaces import IVisualElement


class VisualElement(object):
    implements(IVisualElement)
    descreption = NotImplemented
    label = NotImplemented

    def __init__(self, descreption='', label=''):
        super(VisualElement, self).__init__()
        self.descreption = descreption
        self.label = label
