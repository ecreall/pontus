from deform.widget import SequenceWidget, MappingWidget


class TableWidget(SequenceWidget):
  
    template = 'pontus:templates/table.pt'
    item_template = 'pontus:templates/table_item.pt'
    readonly_template = 'pontus:templates/readonly/table.pt'
    readonly_item_template = 'pontus:templates/readonly/table_item.pt'

class LineWidget(MappingWidget):
  
    template = 'pontus:templates/mapping.pt'
    item_template = 'pontus:templates/mapping_item.pt'
    readonly_template = 'pontus:templates/readonly/mapping.pt'
    readonly_item_template = 'pontus:templates/readonly/mapping_item.pt'  


