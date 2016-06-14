# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

import colander
import transaction
from persistent.dict import PersistentDict
from zope.interface import implementer
from ZODB.blob import Blob
from ZODB.interfaces import BlobError
from PIL import Image as PILImage
from pyramid.threadlocal import get_current_request

from substanced.util import get_oid
from substanced.content import content

from deform.schema import default_widget_makers
from deform.widget import MappingWidget

from substanced.file import File as OriginFile, USE_MAGIC

from dace.util import get_obj
from dace.objectofcollaboration.object import Object as DaceObject

from pontus.interfaces import IFile, IImage


OBJECT_DATA = '_object_data'

OBJECT_OID = '__objectoid__'

NO_VALUES = '_no_values'

MARKER = object()


@content(
    'pontus_file',
    icon='glyphicon glyphicon-file',
    )
@implementer(IFile)
class File(DaceObject, OriginFile):

    def __init__(self, fp, mimetype=None, filename=None, **kwargs):
        if not filename:
            filename = self.title

        DaceObject.__init__(self, **kwargs)
        if fp:
            fp.seek(0)
        else:
            fp = None

        if not mimetype or mimetype == 'application/x-download':
            hint = USE_MAGIC
        else:
            hint = mimetype

        OriginFile.__init__(self, fp, hint, filename)

    @property
    def fp(self):
        return self.blob.open('r')

    @property
    def filename(self):
        return self.title

    @property
    def uid(self):
        return str(get_oid(self, None))

    def get_data(self, node):
        result = {}
        result['filename'] = self.title
        result['uid'] = getattr(self, 'uid', None)
        result['mimetype'] = self.mimetype
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
        if name == 'fp':
            self.blob = Blob()
            self.upload(value, mimetype_hint=USE_MAGIC)
        elif name == 'filename':
            self.title = value
        elif name == 'uid':
            pass
        else:
            super(File, self).__setattr__(name, value)

    @property
    def url(self):
        request = get_current_request()
        return request.resource_url(self)

    def copy(self):
        data = self.get_data(None)
        data.pop('uid')
        return self.__class__(**data)


@content(
    'pontus_image',
    icon='glyphicon glyphicon-picture',
    )
@implementer(IImage)
class Image(File):

    def __init__(self, fp, mimetype=None, filename=None, **kwargs):
        super(Image, self).__init__(fp, mimetype, filename, **kwargs)
        self.set_data(kwargs)

    def get_area_of_interest_dimension(self):
        result = {'x': float(getattr(self, 'x', 0)),
                  'y': float(getattr(self, 'y', 0)),
                  'r': float(getattr(self, 'r', 0))}
        try:
            img = PILImage.open(self.fp)
            result.update({
                  'area_width': float(getattr(self, 'area_width', img.size[1])),
                  'area_height': float(getattr(self, 'area_height', img.size[0]))})
            return result
        except:
            result.update({
                  'area_width': float(getattr(self, 'area_width', 100.0)),
                  'area_height': float(getattr(self, 'area_height', 100.0))})
            return result

    def get_data(self, node):
        result = super(Image, self).get_data(node)
        result.update(self.get_area_of_interest_dimension())
        return result


class Object(colander.SchemaType):

    def serialize(self, node, appstruct):
        if appstruct is None:
            appstruct = colander.null

        if appstruct is not colander.null:
            oid = get_oid(appstruct, None)
            if oid is None:
                return colander.null
            else:
                return str(oid)

        return appstruct

    def deserialize(self, node, cstruct):
        return cstruct


class SetObject(Object):

    def serialize(self, node, appstruct):
        if not appstruct:
            appstruct = colander.null

        if appstruct is not colander.null:
            result = []
            for item in appstruct:
                oid = get_oid(item, None)
                if oid:
                    result.append(str(oid))

            if result:
                return result

            return colander.null

        return appstruct


class ObjectData(colander.Mapping):

    _specialObjects = (File, Image)

    def __init__(self, factory=None, editable=False, unknown='ignore'):
        colander.Mapping.__init__(self, unknown)
        self.factory = factory
        self.editable = editable
        if self.factory is not None and self._is_special_object:
            self.editable = True

    @property
    def _is_special_object(self):
        if self.factory:
            for obj_type in self._specialObjects:
                if obj_type in getattr(self.factory, '__mro__', []):
                    return True

        return False

    def serialize(self, node, appstruct):
        _object = None
        if appstruct is None:
            appstruct = colander.null

        if appstruct is not colander.null and \
            not isinstance(appstruct, (dict, PersistentDict)):
            _object = appstruct
            appstruct = _object.get_data(node)

        result = None
        if not self._is_special_object:
            result = colander.Mapping.serialize(self, node, appstruct)
            if not self.editable or result is colander.null:
                return result
        else:
            if appstruct is colander.null:
                return appstruct

            result = appstruct

        if _object is not None:
            result[OBJECT_OID] = get_oid(_object)

        return result

    def clean_cstruct(self, node, cstruct):
        appstruct = {}
        has_values = False
        if isinstance(cstruct, (dict, PersistentDict)):
            result_copy = dict(cstruct)
            for key, value in result_copy.items():
                subnode = node.get(key)
                missing = getattr(subnode, 'missing', MARKER)
                if (value != missing and \
                    not getattr(subnode, 'to_omit', False)):
                    has_values = True

                if getattr(subnode, 'to_omit', False):
                    if not getattr(subnode, 'private', False):
                        appstruct[key] = value
                        # private is omited and not returned to the user

                    cstruct.pop(key)
                    # don't set data if omitted

        if isinstance(cstruct, (dict, PersistentDict)):
            result_copy = dict(cstruct)
            to_result = {}
            for key, value in result_copy.items():
                is_multiple_cardinality = True
                is_object_type = False
                if not isinstance(value, (list, tuple, set)):
                    value = [value]
                    is_multiple_cardinality = False

                for item in list(value):
                    if isinstance(item, (dict, PersistentDict)) \
                       and OBJECT_DATA in item:
                        is_object_type = True
                        subobject = item.pop(OBJECT_DATA)
                        #to_result.update({key: subobject})
                        if not(key in to_result):
                            to_result[key] = [subobject]
                        else:
                            to_result[key].append(subobject)

                        if not item:
                            value.pop(value.index(item))
                        else:
                            item[OBJECT_DATA] = subobject

                if is_object_type:
                    if is_multiple_cardinality and value:
                        appstruct[key] = value
                    elif value:
                        appstruct[key] = value[0]

                    if is_multiple_cardinality and key in to_result:
                        cstruct[key] = to_result[key]
                    elif key in to_result:
                        cstruct[key] = to_result[key][0]

        return cstruct, appstruct, has_values

    def deserialize(self, node, cstruct):
        obj_oid = None
        if self.editable and cstruct and OBJECT_OID in cstruct:
            obj_oid = cstruct.get(OBJECT_OID, None)
            if not obj_oid or obj_oid == 'None':
                obj_oid = None

        result = None
        if not self._is_special_object:
            result = colander.Mapping.deserialize(self, node, cstruct)
            if not self.editable or \
               result is colander.null or \
               cstruct is colander.null:
                return result
        else:
            if cstruct is colander.null:
                return colander.null

        if result is None:
            result = cstruct

        obj = None
        if obj_oid is not None:
            obj = get_obj(int(obj_oid))

        if self.factory is None and obj is None:
            return result

        result, appstruct, has_values = self.clean_cstruct(node, result)
        if obj is None and self.factory is not None:
            # add form
            obj = self.factory(**result)
            appstruct[NO_VALUES] = not has_values
            appstruct[OBJECT_DATA] = obj
            return appstruct

        # edit form
        obj.set_data(result)
        appstruct[NO_VALUES] = not has_values
        appstruct[OBJECT_DATA] = obj
        return appstruct

    def cstruct_children(self, node, cstruct):
        result = []
        if not self._is_special_object:
            result = colander.Mapping.cstruct_children(self, node, cstruct)
            if result is colander.null or cstruct is colander.null:
                return result
        return result


default_widget_makers[ObjectData] = MappingWidget
