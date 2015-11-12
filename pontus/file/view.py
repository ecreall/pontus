# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

import mimetypes
from pyramid.view import view_config
from pyramid.response import Response

from substanced.file.views import onepixel
from substanced.interfaces import IFile

from pontus.form import FileUploadTempStore


@view_config(
    context=IFile,
    name='',
    )
def view_file(context, request):
    return context.get_response(request=request)


@view_config(
    name='preview_image_upload',
    )
def preview_image_upload(request):
    uid = request.subpath[0]
    tempstore = FileUploadTempStore(request)
    filedata = tempstore.get(uid, {})
    fp = filedata.get('fp')
    filename = ''
    if fp is not None:
        fp.seek(0)
        filename = filedata.get('filename', 'Image')

    mimetype = mimetypes.guess_type(filename, strict=False)[0]
    if not mimetype or not mimetype.startswith('image/'):
        mimetype = 'image/gif'
        fp = open(onepixel, 'rb')
    response = Response(content_type=mimetype, app_iter=fp)
    return response
