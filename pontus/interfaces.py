# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi
from zope.interface import Interface


class IVisualisableElement(Interface):
    pass


class IView(Interface):
    pass


class IFormView(IView):
    pass
