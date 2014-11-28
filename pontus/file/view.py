# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from substanced.interfaces import IFile


@view_config(
    context=IFile,
    name='',
    )
def view_file(context, request):
    return context.get_response(request=request)
