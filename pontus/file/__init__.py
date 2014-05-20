from ZODB.blob import Blob
from ZODB.interfaces import BlobError
import colander
from deform.schema import default_widget_makers
from deform.widget import MappingWidget
import transaction

from substanced.file import File as FL
from substanced.util import get_oid

from dace.util import get_obj
from dace.objectofcollaboration.object import Object as DaceObject

OBJECT_DATA = '_objectdata_' 
ObjectOID = '__objectoid__'


USE_MAGIC = object()


class File(DaceObject,FL):

    def __init__(self, fp, mimetype, filename, preview_url, uid, **kwargs):
        DaceObject.__init__(self)
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

    def get_size(self):
        try:
            return FL.get_size(self)
        except BlobError:
            transaction.commit()
            return FL.get_size(self)

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

    def url(self, request, view=None, args=None):
        if view is None:
            #generalement c est la vue de l index associer qu'il faut retourner
            return request.mgmt_path(self, '@@view')
        else:
            return request.mgmt_path(self, '@@'+view)


class Image(File):
    pass

class Object(colander.SchemaType):

    def serialize(self, node, appstruct):
        if appstruct is None:
            appstruct = colander.null

        if  appstruct is not colander.null:
            return str(get_oid(appstruct))

        return appstruct

    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return  cstruct

        return cstruct


class ObjectData(colander.Mapping):

    __specialObjects = (File, Image)

    def __init__(self, factory=None, editable=False, unknown='ignore'):
        colander.Mapping.__init__(self, unknown)
        self.factory = factory
        self.editable = editable
        if self.factory is not None and self.factory in self.__specialObjects:
            self.editable = True

    def serialize(self, node, appstruct):
        _object = None
        if appstruct is None:
            appstruct = colander.null

        if  appstruct is not colander.null and not isinstance(appstruct, dict):
            _object = appstruct
            appstruct = _object.get_data(node)

        result = None
        if not (self.factory in self.__specialObjects):
            result = colander.Mapping.serialize(self, node, appstruct)
            if not self.editable or result is colander.null:
                return result
        else:
            if appstruct is colander.null:
                return  appstruct

            result = appstruct

        if _object is not None:
            result[ObjectOID] = get_oid(_object)

        return result

    def deserialize(self, node, cstruct):
        obj_oid = None
        if self.editable and cstruct and ObjectOID in cstruct:
            obj_oid = cstruct.get(ObjectOID)

        result = None
        if not (self.factory in self.__specialObjects):
            result = colander.Mapping.deserialize(self, node, cstruct)
            if not self.editable or result is colander.null or cstruct is colander.null:
                return result
        else:
            if cstruct is colander.null:
                return  cstruct

        if result is None:
            result = cstruct

        _object = None
        if isinstance(result, dict) and obj_oid is not None and not (obj_oid=='None') and not (obj_oid==''):
            _object = get_obj(int(obj_oid))

        if self.factory is None and _object is None:
            return result

        omited_result = {}
        if isinstance(result, dict):
            _result = dict(result)
            for (k, n) in _result.items():
                subnode = node.get(k)
                if getattr(subnode, 'to_omit', False):
                     omited_result[k] = n
                     result.pop(k)

        if _object is None and self.factory is not None:
            _object = self.factory(**result)
            if omited_result:
                omited_result[OBJECT_DATA] = _object
                return omited_result

            return _object

        _object.set_data(result)
        if omited_result:
            omited_result[OBJECT_DATA] = _object
            return omited_result

        return _object

    def cstruct_children(self, node, cstruct):
        result = []
        if self.factory is None or not (self.factory in self.__specialObjects):
            result = colander.Mapping.cstruct_children(self, node, cstruct)
            if result is colander.null or cstruct is colander.null:
                return result
        return result


default_widget_makers[ObjectData] = MappingWidget
