# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

from zope.interface import Interface

from substanced.interfaces import IFile as SourceIFile

from dace.interfaces import Attribute


class IVisualisableElement(Interface):

    title = Attribute('title')

    label = Attribute('label')

    description = Attribute('description')


class IFile(SourceIFile):

    filename = Attribute('filename')

    mimetype = Attribute('mimetype')

    size = Attribute('size')

    url = Attribute('url')


class IImage(IFile):
    pass


class IView(Interface):
    pass


class IFormView(IView):
    pass
