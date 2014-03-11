import weakref
from colander import (
    Invalid,
    null,
    )
from deform.widget import (
    SequenceWidget as SW,
    MappingWidget as MW,
    RichTextWidget,
    FileUploadWidget,
    Select2Widget as Select2W,
    OptGroup,
    CheckboxChoiceWidget as CheckboxChoiceW
    )

from deform.compat import (
    string_types,
    url_quote
    )

from translationstring import TranslationString
from substanced.util import get_oid

from pontus.file import __ObjectIndex__
from dace.util import get_obj

class SequenceWidget(SW):


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
                #import pdb; pdb.set_trace()
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


class MappingWidget(MW):

    template = 'pontus:templates/mapping.pt'
    item_template = 'pontus:templates/mapping_item.pt'
    readonly_template = 'pontus:templates/readonly/mapping.pt'
    readonly_item_template = 'pontus:templates/readonly/mapping_item.pt'

    def deserialize(self, field, pstruct):
        data = super(MappingWidget, self).deserialize(field, pstruct)
        if data is null:
            return null

        data[__ObjectIndex__] = pstruct.get(__ObjectIndex__)
        return data


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


class RichTextWidget(RichTextWidget):
  
    template = 'pontus:templates/richtext.pt' 


class MemoryTmpStore(dict):
    def preview_url(self, name):
        return None


class FileWidget(FileUploadWidget):

    template = 'pontus:file/templates/file_upload.pt'

    def __init__(self, **kw):
        tmpstro= MemoryTmpStore()
        FileUploadWidget.__init__(self,tmpstro, **kw)

    def deserialize(self, field, pstruct):
        data = super(FileWidget, self).deserialize(field, pstruct)
        if data is null:
            return null

        data[__ObjectIndex__] = pstruct.get(__ObjectIndex__)
        return data


def _normalize_choices(values):
    result = []
    for item in values:
        if isinstance(item, OptGroup):
            normalized_options = _normalize_choices(item.options)
            result.append(OptGroup(item.label, *normalized_options))
        else:
            value, description = item
            if not isinstance(value, string_types):
                value = str(get_oid(value))
            result.append((value, description))
    return result


class Select2Widget(Select2W):

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = self.null_value
        readonly = kw.get('readonly', self.readonly)
        values = kw.get('values', self.values)
        template = readonly and self.readonly_template or self.template
        kw['values'] = _normalize_choices(values)
        tmpl_values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **tmpl_values)

    def deserialize(self, field, pstruct):
        if pstruct in (null, self.null_value):
            return null

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

        return result


class CheckboxChoiceWidget(CheckboxChoiceW):

    #template = 'pontus:templates/checkbox_choice.pt'

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ()
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
