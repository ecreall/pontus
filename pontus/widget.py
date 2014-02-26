from deform.widget import SequenceWidget, MappingWidget as MW, RichTextWidget, FileUploadWidget
from colander import null
from pontus.file import __ObjectIndex__


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
