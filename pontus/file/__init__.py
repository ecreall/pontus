from ZODB.blob import Blob
from ZODB.interfaces import BlobError
import colander
from deform.schema import default_widget_makers
from deform.widget import MappingWidget
import transaction

from substanced.file import File as OriginFile
from substanced.util import get_oid

from dace.util import get_obj
from dace.objectofcollaboration.object import Object as DaceObject

OBJECT_DATA = '_object_data'
OBJECT_OID = '__objectoid__'
NO_VALUES = '_no_values'

USE_MAGIC = object()

MARKER = object()


class File(DaceObject, OriginFile):

    def __init__(self, fp, mimetype, filename, preview_url, uid, **kwargs):
        DaceObject.__init__(self, **kwargs)
        if fp:
            fp.seek(0)
        else:
            fp = None
        mimetype = mimetype or USE_MAGIC
        OriginFile.__init__(self, fp, mimetype, filename)
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
            return OriginFile.get_size(self)
        except BlobError:
            transaction.commit()
            return OriginFile.get_size(self)

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
            return request.resource_url(self, '@@view')
        else:
            return request.resource_url(self, '@@'+view)

    def get_response(self, **kw):
        response = super(File, self).get_response(**kw)
        response.content_disposition = 'attachment; filename="%s"' % self.filename
        return response


class Image(File):
    pass

class Object(colander.SchemaType):

    def serialize(self, node, appstruct):
        if appstruct is None:
            appstruct = colander.null

        if appstruct is not colander.null:
            oid = get_oid(appstruct)
            if oid is None:
                return colander.null
            else:
                return str(oid)

        return appstruct

    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return cstruct

        return cstruct


class ObjectData(colander.Mapping):

    _specialObjects = (File, Image)

    def __init__(self, factory=None, editable=False, unknown='ignore'):
        colander.Mapping.__init__(self, unknown)
        self.factory = factory
        self.editable = editable
        if self.factory is not None and self.factory in self._specialObjects:
            self.editable = True

    def serialize(self, node, appstruct):
        _object = None
        if appstruct is None:
            appstruct = colander.null

        if  appstruct is not colander.null and not isinstance(appstruct, dict):
            _object = appstruct
            appstruct = _object.get_data(node)

        result = None
        if self.factory is not None and not self.factory in self._specialObjects:
            result = colander.Mapping.serialize(self, node, appstruct)
            if not self.editable or result is colander.null:
                return result
        else:
            if appstruct is colander.null:
                return  appstruct

            result = appstruct

        if _object is not None:
            result[OBJECT_OID] = get_oid(_object)

        return result

    def deserialize(self, node, cstruct):
        result = None
        if self.factory is not None and not self.factory in self._specialObjects:
            result = colander.Mapping.deserialize(self, node, cstruct)
            if not self.editable or result is colander.null or cstruct is colander.null:
                return result
        elif cstruct is colander.null:
            return cstruct

        if result is None:
            result = cstruct

        obj = None
        if isinstance(result, dict) and self.editable:
            obj_oid = result.get(OBJECT_OID, None)
            if obj_oid == 'None':
                obj_oid = None

            if obj_oid is not None:
                obj = get_obj(int(obj_oid))

        if self.factory is None and obj is None:
            return result

        appstruct = {}
        has_values = False
        if isinstance(result, dict):
            data_to_set = {}
            for key, value in result.items():
                subnode = node.get(key)
                if key in ('_csrf_token_', OBJECT_OID):
                    continue

                missing = getattr(subnode, 'missing', MARKER)
                if value != missing:
                    has_values = True

                if getattr(subnode, 'to_omit', False):
                    if not getattr(subnode, 'private', False):
                        appstruct[key] = value

                    continue  # don't set data if omitted

                data_to_set[key] = value

                if not isinstance(value, (list, tuple)):
                    if isinstance(value, dict) and OBJECT_DATA in value:
                        subobject = value[OBJECT_DATA]
                        appstruct[key] = subobject
                else:
                    for item in value:
                        if isinstance(item, dict) and OBJECT_DATA in item:
                            subobject = item[OBJECT_DATA]
                            appstruct.setdefault(key, []).append(subobject)

        if obj is None:
            # add form
            if self.factory is not None:
                appstruct[NO_VALUES] = not has_values
                appstruct[OBJECT_DATA] = self.factory(**data_to_set)
        else:
            # edit form
            obj.set_data(data_to_set)
            appstruct[NO_VALUES] = not has_values
            appstruct[OBJECT_DATA] = obj

        return appstruct


    def cstruct_children(self, node, cstruct):
        result = []
        if self.factory is None or not self.factory in self._specialObjects:
            result = colander.Mapping.cstruct_children(self, node, cstruct)
            if result is colander.null or cstruct is colander.null:
                return result
        return result


default_widget_makers[ObjectData] = MappingWidget
