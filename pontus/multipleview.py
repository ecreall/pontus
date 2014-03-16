# -*- coding: utf-8 -*-
from pontus.view import View, merg_dicts


def default_builder(parent, views):
    if views is None:
        return

    for view in views:
        if isinstance(view, tuple):
            viewinstance = MultipleView(parent.context, parent.request, parent, parent.wizard, parent.index)
            viewinstance.merged = parent.merged
            if parent.merged:
                viewinstance.coordiantes = parent.coordiantes

            viewinstance.title = view[0]
            viewinstance.viewid = parent.viewid+'_'+viewinstance.title.replace(' ','-')
            viewinstance.builder(view[1])
            parent.children.append(viewinstance)
        else:
            viewinstance = view(parent.context, parent.request, parent, parent.wizard, parent.index)
            if parent.merged:
                viewinstance.coordiantes = parent.coordiantes

            parent.children.append(viewinstance)        


class MultipleView(View):

    views = ()
    builder = default_builder
    merged = False
    item_template = 'templates/submultipleview.pt'
    self_template = 'templates/submultipleview.pt'
    
    def __init__(self, context, request, parent=None, wizard=None, index=0):
        super(MultipleView, self).__init__(context, request, parent, wizard, index)
        self.children = []
        self._coordiantes = []
        self.builder(self.views)

    def _activate(self, items):
        if items:
            item = items[0]
            item['isactive'] = True
            if 'items' in item:
                self._activate(item['items'])

    def update(self,):
        result = {}
        for view in self.children:
            view_result = view.update()

            if view.finished_successfully:
                self.finished_successfully = True

            if not isinstance(view_result,dict):
                return view_result

            result = merg_dicts(view_result, result)

        for coordiante in result['coordiantes']:
            items = result['coordiantes'][coordiante]
            isactive = False
            for item in items:
                if item['isactive']:
                    isactive = True
                    break
            
            if not isactive:
                self._activate(items)
                if self.parent is None:
                    isactive = True

            result['coordiantes'][coordiante] = [{'isactive':isactive,
                                      'items': items,
                                      'view': self,
                                      'id':self.viewid}]

        return result
