from deform.widget import SequenceWidget, MappingWidget


class TableWidget(SequenceWidget):
  
    template = 'sdkuneagi:templates/table.pt'
    item_template = 'sdkuneagi:templates/table_item.pt'
    readonly_template = 'sdkuneagi:templates/readonly/table.pt'
    readonly_item_template = 'sdkuneagi:templates/readonly/table_item.pt'

class LineWidget(MappingWidget):
  
    template = 'sdkuneagi:templates/mapping.pt'
    item_template = 'sdkuneagi:templates/mapping_item.pt'
    readonly_template = 'sdkuneagi:templates/readonly/mapping.pt'
    readonly_item_template = 'sdkuneagi:templates/readonly/mapping_item.pt'  


