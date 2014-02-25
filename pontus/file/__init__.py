from ZODB.blob import Blob
import colander
import deform.widget
from deform.i18n import _

from substanced.file import File as FL
from substanced.util import get_oid
from dace.util import get_obj
from dace.object import Object


USE_MAGIC = object()


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
  
    def serialize(self, node, appstruct):
        obj = None
        if  appstruct is not colander.null and not isinstance(appstruct, dict):
            obj = appstruct
            appstruct = obj.get_data(node)

        result = None
        if not (self.factory in self.__specialObjects):
            result = colander.Mapping.serialize(self, node, appstruct)
            if result is colander.null:
                return result
        else:
            if appstruct is colander.null:
                return  appstruct  

        if result is None:
            result = appstruct
        
        if isinstance(result, dict) and obj is not None:
            result['oid'] = str(get_oid(obj))
        
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
        import pdb; pdb.set_trace()
        oid = None
        if result and result.get('oid') is not None and not (result.get('oid')==''):
                oid = int(result.get('oid'))
        
        obj = None
        if oid is not None:
            obj = get_obj(oid)
        else :
            obj = self.factory(**result)
            #result['__object__'] = obj
            #return result
            return obj
        
        for name, val in result.items():
            if getattr(obj, name, None) is not None:
                existing_val = getattr(obj, name, None)
                new_val = result[name]
                if existing_val != new_val:
                    setattr(obj, name, new_val)
        #result['__object__'] = obj
        #return result
        return obj


    def cstruct_children(self, node, cstruct):
        result = []
        if not (self.factory in self.__specialObjects):
            result = colander.Mapping.cstruct_children(self, node, cstruct)
            if result is colander.null or cstruct is colander.null:
                return result
        return result
