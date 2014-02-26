from ZODB.blob import Blob
import colander
import deform.widget
from deform.i18n import _

from substanced.file import File as FL
from substanced.util import get_oid
from dace.util import get_obj
from dace.object import Object


USE_MAGIC = object()
__ObjectIndex__ = '__objectid__'

class File(Object,FL):

    def __init__(self, fp, mimetype, filename, preview_url, uid, **kwargs):
        Object.__init__(self)
        if fp:
            fp.seek(0)
        else:
            fp = None
        mimetype = mimetype or USE_MAGIC
        FL.__init__(self, fp, mimetype, filename)
        self.preview_url = preview_url
        self.uid = uid

    @property
    def fp(self):
        return self.blob.open('r')

    @property
    def filename(self):
        return self.title
        
    def get_data(self, node):
        result = {}
        result['filename'] = self.title
        result['uid'] = self.uid
        result['mimetype'] = self.mimetype
        result['preview_url'] = self.preview_url
        result['size'] = self.get_size()
        result['fp'] = self.blob.open('r')
        return result

    def __setattr__(self, name, value):
        if name == 'mimetype':
            if value is USE_MAGIC:
                super(File,self).__setattr__('mimetype', 'application/octet-stream')
            else:
                val = value or 'application/octet-stream'
                super(File,self).__setattr__('mimetype', val)

        elif name == 'fp':
            if self.mimetype is USE_MAGIC:
                hint = USE_MAGIC
            else:
                hint = None

            self.blob = Blob()
            self.upload(value, mimetype_hint=hint)
        elif name == 'filename':
            self.title = value
        else:
            super(File,self).__setattr__(name, value)


class ObjectData(colander.Mapping):

    __specialObjects = (File,)

    def __init__(self, factory, unknown='ignore'):
        colander.Mapping.__init__(self, unknown)
        self.factory = factory
        self.context = None
  
    def serialize(self, node, appstruct):
        _object = None
        if  appstruct is not colander.null and not isinstance(appstruct, dict):
            if node.widget is None:
                self.context  = appstruct

            _object = appstruct
            appstruct = _object.get_data(node)

        result = None
        if not (self.factory in self.__specialObjects):
            result = colander.Mapping.serialize(self, node, appstruct)
            if result is colander.null:
                return result
        else:
            if appstruct is colander.null:
                return  appstruct  
            result = appstruct

        if _object is not None:
            result[__ObjectIndex__] = get_oid(_object)

        return result

    def deserialize(self, node, cstruct):
        result = None
        if not (self.factory in self.__specialObjects):
            result = colander.Mapping.deserialize(self, node, cstruct)
            if result is colander.null or cstruct is colander.null:
                return result
        else:
            if cstruct is colander.null:
                return  cstruct 

        if result is None:
            result = cstruct

        _object = None
        if isinstance(result, dict) and result.get(__ObjectIndex__) is not None:
            _object = get_obj(int(result.get(__ObjectIndex__)))
        elif self.context is not None:
            _object = self.context
            
        if _object is None:
            _object = self.factory(**result)
            return _object
        
        for name, val in result.items():
            if getattr(_object, name, None) is not None:
                existing_val = getattr(_object, name, None)
                new_val = result[name]
                if existing_val != new_val:
                    setattr(_object, name, new_val)

        return _object

    def cstruct_children(self, node, cstruct):
        result = []
        if not (self.factory in self.__specialObjects):
            result = colander.Mapping.cstruct_children(self, node, cstruct)
            if result is colander.null or cstruct is colander.null:
                return result
        return result
