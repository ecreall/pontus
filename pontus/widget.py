# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

import weakref
import colander
from persistent.list import PersistentList
from pyramid.threadlocal import get_current_request
from translationstring import TranslationString
from colander import (
    Invalid,
    null,
    )
from deform.i18n import _
from deform.widget import (
    SequenceWidget as OriginSequenceWidget,
    MappingWidget as OriginMappingWidget,
    RichTextWidget,
    FileUploadWidget,
    TextInputWidget as OriginTextInputWidget,
    OptGroup,
    FormWidget as OriginFormWidget,
    SelectWidget as OriginSelectWidget,
    CheckboxChoiceWidget as OriginCheckboxChoiceWidget,
    default_resource_registry
    )
from deform.compat import (
    string_types,
    url_quote
    )
from substanced.file import FileUploadTempStore
from substanced.util import get_oid

from dace.util import get_obj

from pontus.file import OBJECT_OID
from pontus import log


class TextInputWidget(OriginTextInputWidget):

    template = 'pontus:templates/textinput.pt'
    readonly_template = 'pontus:templates/readonly/textinput.pt'


class MappingWidget(OriginMappingWidget):

    template = 'pontus:templates/mapping.pt'


class SequenceWidget(OriginSequenceWidget):

    template = 'pontus:templates/sequence.pt'
    item_template = 'pontus:templates/sequence_item.pt'
    requirements = (('deform', None), 
                    ('sortable', None), 
                    ('sequence_pontus', None))


    def prototype(self, field):
        # we clone the item field to bump the oid (for easier
        # automated testing; finding last node)
        item_field = field.children[0].clone()
        # root ++ Ecreall++ Amen
        if field.children[0].parent is not None:
            item_field._parent = weakref.ref(field.children[0].parent)
        # root ++ Ecreall++ Amen
        if not item_field.name:
            info = 'Prototype for %r has no name' % field
            raise ValueError(info)
        # NB: item_field default should already be set up
        proto = item_field.render_template(self.item_template, parent=field)
        if isinstance(proto, string_types):
            proto = proto.encode('utf-8')
        proto = url_quote(proto)
        return proto

    def serialize(self, field, cstruct, **kw):
        # XXX make it possible to override min_len in kw

        if cstruct in (null, None):
            if self.min_len is not None:
                cstruct = [null] * self.min_len
            else:
                cstruct = []

        cstructlen = len(cstruct)

        if self.min_len is not None and (cstructlen < self.min_len):
            cstruct = list(cstruct) + ([null] * (self.min_len-cstructlen))

        item_field = field.children[0]

        if getattr(field, 'sequence_fields', None):
            # this serialization is being performed as a result of a
            # validation failure (``deserialize`` was previously run)
            assert(len(cstruct) == len(field.sequence_fields))
            subfields = list(zip(cstruct, field.sequence_fields))
        else:
            # this serialization is being performed as a result of a
            # first-time rendering
            subfields = []
            for val in cstruct:
                cloned = item_field.clone()
                # root ++ Ecreall++ Amen
                if item_field.parent is not None:
                    cloned._parent = weakref.ref(item_field.parent)
                # root ++ Ecreall++ Amen
                if val is not null:
                    # item field has already been set up with a default by
                    # virtue of its constructor and setting cstruct to null
                    # here wil overwrite the real default
                    cloned.cstruct = val
                subfields.append((cloned.cstruct, cloned))

        readonly = kw.get('readonly', self.readonly)
        template = readonly and self.readonly_template or self.template
        translate = field.translate
        subitem_title = kw.get('subitem_title', item_field.title)
        subitem_description = kw.get(
            'subitem_description',
            item_field.description
            )
        add_subitem_text_template = kw.get(
            'add_subitem_text_template',
            self.add_subitem_text_template
            )
        add_template_mapping = dict(
            subitem_title=translate(subitem_title),
            subitem_description=translate(subitem_description),
            subitem_name=item_field.name,
            )
        if isinstance(add_subitem_text_template, TranslationString):
            add_subitem_text = add_subitem_text_template % add_template_mapping
        else:
            add_subitem_text = _(add_subitem_text_template,
                                 mapping=add_template_mapping)

        kw.setdefault('subfields', subfields)
        kw.setdefault('add_subitem_text', add_subitem_text)
        kw.setdefault('item_field', item_field)

        values = self.get_template_values(field, cstruct, kw)

        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        result = []
        error = None

        if pstruct is null:
            pstruct = []

        field.sequence_fields = []
        item_field = field.children[0]

        for num, substruct in enumerate(pstruct):
            subfield = item_field.clone()
            if item_field.parent is not None:
                subfield._parent = weakref.ref(item_field.parent)
            try:
                subval = subfield.deserialize(substruct)
            except Invalid as e:
                subval = e.value
                if error is None:
                    error = Invalid(field.schema, value=result)
                error.add(e, num)

            subfield.cstruct = subval
            result.append(subval)
            field.sequence_fields.append(subfield)

        if error is not None:
            raise error

        return result


class TableWidget(SequenceWidget):

    template = 'pontus:templates/table.pt'
    item_template = 'pontus:templates/table_item.pt'
    readonly_template = 'pontus:templates/readonly/table.pt'
    readonly_item_template = 'pontus:templates/readonly/table_item.pt'


class LineWidget(MappingWidget):

    template = 'pontus:templates/line_mapping.pt'
    item_template = 'pontus:templates/line_mapping_item.pt'
    readonly_template = 'pontus:templates/readonly/line_mapping.pt'
    readonly_item_template = 'pontus:templates/readonly/line_mapping_item.pt'


class AccordionWidget(SequenceWidget):

    template = 'pontus:templates/accordion.pt'
    item_template = 'pontus:templates/accordion_item.pt'


class RichTextWidget(RichTextWidget):
    default_options = (('height', 240),
                       ('width', 0),
                       ('skin', 'lightgray'),
                       ('fontsize_formats', "8pt 9pt 10pt 11pt 12pt 13pt 14pt 15pt 26pt 36pt"),
                       ('toolbar', "preview print | undo redo | fontselect fontsizeselect | forecolor backcolor | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent"),
                       ('theme', 'modern'),
                       ('mode', 'exact'),
                       ('strict_loading_mode', True),
                       ('remove_linebreaks', False),
                       ('theme_advanced_resizing', True),
                       ('theme_advanced_toolbar_align', 'left'),
                       ('theme_advanced_toolbar_location', 'top')) 

    template = 'pontus:templates/richtext.pt'


class MemoryTmpStore(dict):
    def preview_url(self, name):
        return None


class FileWidget(FileUploadWidget):

    template = 'pontus:file/templates/file_upload.pt'
    requirements = (('file_upload', None),)

    def __init__(self, **kw):
        if 'tmpstore' not in kw:
            kw['tmpstore'] = MemoryTmpStore()

        FileUploadWidget.__init__(self, **kw)

    @property
    def request(self):
        return get_current_request()

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = {}

        if cstruct and 'uid' in cstruct:
            uid = cstruct['uid']
            if 'fp' in cstruct:
                try:
                    cstruct['fp'].seek(0)
                except Exception:
                    pass

            if not hasattr(self, 'uids'):
                setattr(self, 'uids', {})

            if uid not in self.tmpstore or \
               not self.tmpstore.get(uid, {}).get('fp', None):
                self.tmpstore[uid] = cstruct

            self.uids[field] = uid

        readonly = kw.get('readonly', self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        form = field.get_root()
        form.stores = getattr(form, 'stores', [])
        form.stores.append(self.tmpstore)
        data = super(FileWidget, self).deserialize(field, pstruct)
        file_oid = pstruct.get(OBJECT_OID, 'None')
        file_oid = file_oid if file_oid != 'None' else None
        if pstruct.get('_object_removed', 'false') == 'true':
            return null

        if data is null and not file_oid:
            return null
        elif data is null:
            data = {}

        if file_oid:
            try:
                data[OBJECT_OID] = file_oid
                if 'fp' not in data:
                    file_obj = get_obj(int(file_oid))
                    data['fp'] = file_obj.fp
            except Exception:
                pass

        try:
            if 'fp' in data:
                data['fp'].seek(0)
        except Exception:
            pass

        if not data:
            return null

        return data


class ImageWidget(FileWidget):

    template = 'pontus:file/templates/img_upload.pt'
    requirements = (('img_upload', None),)

    def preview_url(self, field):
        img_src = None
        uid = getattr(self, 'uids', {}).get(field, None)
        if uid:
            if uid and not isinstance(self.tmpstore, MemoryTmpStore):
                filedata = self.tmpstore.get(uid, {})
                if 'fp' in filedata:
                    img_src = self.tmpstore.preview_url(uid)

        if img_src is None and getattr(self, 'source', None):
            img_src = getattr(self, 'source').url

        return img_src

    def deserialize(self, field, pstruct):
        data = super(ImageWidget, self).deserialize(field, pstruct)
        if data is null:
            return null

        if 'upload' in pstruct:
            pstruct.pop('upload')

        if OBJECT_OID in pstruct:
            pstruct.pop(OBJECT_OID)

        data.update(pstruct)
        try:
            data['x'] = float(data['x']) if 'x' in data else 10.0
        except ValueError as error:
            log.warning(error)
            data['x'] = 10.0

        try:
            data['y'] = float(data['y']) if 'y' in data else 10.0
        except ValueError as error:
            log.warning(error)
            data['y'] = 10.0

        try:
            data['r'] = float(data['r']) if 'r' in data else 0.0
        except ValueError as error:
            log.warning(error)
            data['r'] = 0.0

        try:
            data['area_height'] = float(data['area_height']) if 'area_height' in data else 100.0
        except ValueError as error:
            log.warning(error)
            data['area_height'] = 100.0

        try:
            data['area_width'] = float(data['area_width']) if 'area_width' in data else 100.0
        except ValueError as error:
            log.warning(error)
            data['area_width'] = 100.0

        return data


@colander.deferred
def image_upload_widget(node, kw):
    request = node.bindings['request']
    tmpstore = FileUploadTempStore(request)
    return ImageWidget(tmpstore)


def _normalize_choices(values):
    result = []
    for item in values:
        if isinstance(item, OptGroup):
            normalized_options = _normalize_choices(item.options)
            result.append(OptGroup(item.label, *normalized_options))
        else:
            value, description = item
            if not isinstance(value, string_types):
                try:
                    value = str(get_oid(value))
                except Exception:
                    value = str(value)

            if not(value in dict(result)): 
                result.append((value, description))

    return result

 
class SelectWidget(OriginSelectWidget):

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            if hasattr(self, 'pstruct') and field in self.pstruct:
                cstruct = self.pstruct[field]
            else:    
                cstruct = self.null_value

        if cstruct and getattr(self, 'multiple', False):
            result = []
            for value in list(cstruct):
                try:
                    result.append(str(get_oid(value)))
                except Exception:
                    result.append(value)

            cstruct = result
        elif not isinstance(cstruct, string_types):
            try:
                cstruct = str(get_oid(cstruct))
            except Exception:
                pass

        if cstruct:
            title_getter = getattr(self, 'title_getter', default_title_getter)
            dict_values = dict(self.values)
            if isinstance(cstruct, (list, PersistentList, tuple, set)):
                ignored_values = [c for c in cstruct if c not in dict_values]
                if ignored_values:
                    self.values.extend([(val_id, title_getter(val_id)) \
                                            for val_id in ignored_values])
            else:
                if cstruct not in dict_values:
                    self.values.append(
                         (cstruct, title_getter(cstruct)))

        readonly = kw.get('readonly', self.readonly)
        values = kw.get('values', self.values)
        template = readonly and self.readonly_template or self.template
        kw['values'] = _normalize_choices(values)
        tmpl_values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **tmpl_values)

    def deserialize(self, field, pstruct):
        pstruct = super(SelectWidget, self).deserialize(field, pstruct)
        if pstruct in (null, self.null_value):
            return null

        if isinstance(pstruct, string_types):
            ob = None
            self.pstruct = {}
            self.pstruct[field] = pstruct
            try:
                ob = get_obj(int(pstruct))
                if ob is None:
                    return pstruct
                else:
                    return ob
            except ValueError:
                return pstruct
        else:
            result = []
            for item in pstruct:
                ob = None
                try:
                    ob = get_obj(int(item))
                    if ob is None:
                        result.append(item)
                    else:
                        result.append(ob)
                except ValueError:
                    result.append(item)

            if not result:
                return null

            self.pstruct = {}
            self.pstruct[field] = result
            return result


class Select2Widget(SelectWidget):
    template = 'pontus:templates/select2.pt'
    requirements = (('deform', None), ('select2creation', None))
    create = False


def default_title_getter(id):
    return id


class AjaxSelect2Widget(Select2Widget):
    template = 'pontus:templates/ajax_select2.pt'
    requirements = ( ('ajaxselect2', None),) 

    @property
    def request(self):
        return get_current_request()


class RadioChoiceWidget(SelectWidget):
    template = 'deform:templates/radio_choice.pt'
    readonly_template = 'deform:templates/readonly/radio_choice.pt'

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = self.null_value

        if getattr(self, 'multiple', False) and \
           not isinstance(cstruct, (tuple, list)):
                cstruct = [cstruct]

        return super(RadioChoiceWidget, self).serialize(field, cstruct, **kw)

    def deserialize(self, field, pstruct):
        if pstruct in (null, self.null_value):
            return null

        if not getattr(self, 'multiple', False) and \
           isinstance(pstruct, (list, tuple)):
            pstruct = pstruct[0]

        try:
            return get_obj(int(pstruct))
        except ValueError:
            return pstruct


class CheckboxChoiceWidget(OriginCheckboxChoiceWidget):


    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ()

        is_multiple = getattr(self, 'multiple', False)
        if is_multiple and not isinstance(cstruct, (list, tuple, set)):
            cstruct = [cstruct]

        if cstruct and is_multiple and \
           not isinstance(list(cstruct)[0], string_types):
            try:
                cstruct = [str(get_oid(value)) for value in cstruct]
            except Exception:
                pass
        elif isinstance(cstruct, string_types):
            try:
                cstruct = str(get_oid(cstruct))
            except Exception:
                pass

        readonly = kw.get('readonly', self.readonly)
        values = kw.get('values', self.values)
        kw['values'] = _normalize_choices(values)
        template = readonly and self.readonly_template or self.template
        tmpl_values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **tmpl_values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null

        if not isinstance(pstruct, (list, tuple)):
            pstruct = (pstruct,)

        if isinstance(pstruct, string_types):
            return pstruct
        else:
            result = []
            for item in pstruct:
                ob = None
                try:
                    ob = get_obj(int(item))
                    if ob is None:
                        result.append(item)
                    else:
                        result.append(ob)
                except ValueError:
                    result.append(item)

            return tuple(result)


class SimpleMappingWidget(MappingWidget):

    template = 'pontus:templates/simple_mapping.pt'


class SimpleFormWidget(OriginFormWidget):

    item_template = 'pontus:templates/simple_mapping_item.pt'


class Length(object):
    """ Validator which succeeds if the value passed to it has a
    length between a minimum and maximum.  The value is most often a
    string."""
    def __init__(self, _, min=None, max=None,
                 min_message='Shorter than minimum length ${min}',
                 max_message='Longer than maximum length ${max}'):
        self.min = min
        self.max = max
        self.min_message = min_message
        self.max_message = max_message
        self.translationStringFactory = _

    def __call__(self, node, value):
        if self.min is not None:
            if len(value) < self.min:
                min_err = self.translationStringFactory(
                              self.min_message.format(min=self.min))
                raise Invalid(node, min_err)

        if self.max is not None:
            if len(value) > self.max:
                max_err = self.translationStringFactory(
                              self.max_message.format(max=self.max))
                raise Invalid(node, max_err)


default_resource_registry.set_js_resources('select2creation', None, 
               'pontus:static/select2/dist/js/select2.js' )


default_resource_registry.set_css_resources('select2creation', None, 
               'pontus:static/select2/dist/css/select2.min.css' )


default_resource_registry.set_js_resources('ajaxselect2', None, 
               'pontus:static/select2/dist/js/select2.js', 
               'pontus:static/js/select2_ajax_extension.js')


default_resource_registry.set_css_resources('ajaxselect2', None, 
              'pontus:static/select2/dist/css/select2.min.css')


default_resource_registry.set_css_resources('sequence_pontus', None, 
              'pontus:static/css/sequence_widget.css')

default_resource_registry.set_js_resources('file_upload', None, 
               'pontus:static/js/file_upload.js',
               'pontus:static/kartik-v-bootstrap-fileinput/js/fileinput.js' )

default_resource_registry.set_css_resources('file_upload', None, 
              'pontus:static/kartik-v-bootstrap-fileinput/css/fileinput.min.css')

default_resource_registry.set_js_resources('img_upload', None, 
               'pontus:static/js/img_upload.js',
               'pontus:static/cropper-master/dist/cropper.js' )

default_resource_registry.set_css_resources('img_upload', None, 
              'pontus:static/css/img_upload.css',
               'pontus:static/cropper-master/dist/cropper.css')
