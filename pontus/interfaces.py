# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi

"""Public contracts: visualisable elements, files/images, views."""
from zope.interface import Interface

from substanced.interfaces import IFile as SourceIFile

from dace.interfaces import Attribute


class IVisualisableElement(Interface):

    """Title/label/description contract of displayable contents."""
    title = Attribute('title')

    label = Attribute('label')

    description = Attribute('description')


class IFile(SourceIFile):

    """A stored file: filename, mimetype, size, url."""
    filename = Attribute('filename')

    mimetype = Attribute('mimetype')

    size = Attribute('size')

    url = Attribute('url')


class IImage(IFile):
    """A stored image (file with variants and crop area)."""
    pass


class IView(Interface):
    """Marker of pontus views."""
    pass


class IFormView(IView):
    """Marker of pontus form views."""
    pass
