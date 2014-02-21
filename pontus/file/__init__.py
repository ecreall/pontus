from ZODB.blob import Blob
import colander
import deform.widget
from deform.i18n import _

from substanced.file import File as FL
from substanced.util import get_oid
from dace.util import get_obj


USE_MAGIC = object()


class File(FL):

    def __init__(self, stream, mimetype, title, preview_url, uid):
        FL.__init__(self, stream, mimetype, title)
        self.preview_url = preview_url
        self.uid = uid
        
    def getdata(self):
        result = {}
        result['filename'] = self.title
        result['uid'] = self.uid
        result['mimetype'] = self.mimetype
        result['preview_url'] = self.preview_url
        result['oid'] = str(get_oid(self))
        result['size'] = self.get_size()
        result['fp'] = self.blob.open('r')
        return result

    def setdata(self, data):
        self.title = data['filename']
        self.uid = data['uid']
        self.preview_url = data['preview_url']
        mimetype = data['mimetype']
        if mimetype is USE_MAGIC:
            self.mimetype = 'application/octet-stream'
        else:
            self.mimetype = mimetype or 'application/octet-stream'

        stream = data['fp']
        if stream is not None:
            if mimetype is USE_MAGIC:
                hint = USE_MAGIC
            else:
                hint = None
            self.blob = Blob()
            self.upload(stream, mimetype_hint=hint)


class FileData(object):


    def serialize(self, node, value):
        if value is colander.null:
            return colander.null

        value = value.getdata()
        if not hasattr(value, 'get'):
            mapping = {'value':repr(value)}
            raise colander.Invalid(
                node,
                _('${value} is not a dictionary', mapping=mapping)
                )
        for n in ('filename', 'uid'):
            if not n in value:
                mapping = {'value':repr(value), 'key':n}
                raise colander.Invalid(
                    node,
                    _('${value} has no ${key} key', mapping=mapping)
                    )
        result = deform.widget.filedict(value)
        # provide a value for these entries even if None
        result['mimetype'] = value.get('mimetype')
        result['size'] = value.get('size')
        result['fp'] = value.get('fp')
        result['oid'] = value.get('oid')
        result['preview_url'] = value.get('preview_url')
        return result

    def deserialize(self, node, value):
        myfile = None
        mimetype = None
        stream = None
        name = None
        uid = None
        oid = None
        preview_url = None
        if value:
            mimetype = value.get('mimetype') or USE_MAGIC
            name = value.get('filename')
            stream =value.get('fp')
            uid = value.get('uid')
            if value.get('oid') is not None and not (value.get('oid')==''):
                oid = int(value.get('oid'))

            preview_url = value.get('preview_url')
            if stream:
                stream.seek(0)
            else:
                stream = None
        
        if oid is not None:
            myfile = get_obj(oid)
        else :
            return File(stream, mimetype, name, preview_url, uid)

        myfile.setdata(value)
        return myfile


    def cstruct_children(self, node, cstruct): # pragma: no cover
        return []
