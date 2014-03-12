from zope.interface import implements
from zope.interface import providedBy

from pyramid.threadlocal import get_current_registry
from pyramid.interfaces import IView as IV, IViewClassifier
from pyramid import renderers
from pyramid.renderers import get_renderer
from pyramid.path import package_of
from pyramid_layout.layout import Structure

from pontus.interfaces import IView
from pontus.wizard import Step

__emptytemplate__ = 'templates/empty.pt'

class View(Step):
    implements(IView)

    viewid = ''
    slot = 'main'
    item_template = 'templates/subview.pt'
    self_template = None

    def render_item(self, item, slot):
        body = renderers.render(self.item_template, {'slot':slot,'subitem':item}, self.request)
        return Structure(body)

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        Step.__init__(self, wizard, index)
        self.context = context
        self.request = request
        self.parent = parent
        if self.parent is not None:
            self.viewid = self.parent.viewid+'_'+self.viewid

    def __call__(self):
        result = self.update()
        if isinstance(result, dict):
            if not ('js_links' in result):
                result['js_links'] = []

            if not ('css_links' in result):
                result['css_links'] = []

        return result
  
    def update(self,):
        pass

    def content(self, result, template=None, main_template=None):
        if template is None:
            registry = get_current_registry()
            context_iface = providedBy(self.context)
            view_deriver = registry.adapters.lookup((IViewClassifier, self.request.request_iface, context_iface), IV, name=self.title, default=None)
            discriminator = view_deriver.__discriminator__().resolve()
            template = registry.introspector.get('templates', discriminator).title

        if main_template is None:
            main_template = get_renderer(__emptytemplate__).implementation()

        if isinstance(result, dict):
            result['main_template'] = main_template

        body = renderers.render(template, result, self.request)
        return {'body':body,
                'args':result,
               }

    def adapt_item(self, render, id, isactive=True):
        if self.parent is not None:
            isactive = False

        item = {'view':self, 'id':id, 'isactive':isactive}
        if isinstance(render, list):
            item['items'] = render
        else:
            item['body'] = render

        return item
  
    def setviewid(self, viewid):
        self.viewid = viewid


class CallView(View):
    view = None
    self_template = 'pontus:templates/global_accordion.pt'

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        View.__init__(self, context, request, parent, wizard, index, **kwargs)
        items = self.get_items()
        if not isinstance(items, (list, tuple)):
            items = [items]

        self.children = [self.view(item_context, request, self, None, None,**kwargs) for item_context in items]
        for i, v in enumerate(self.children):
            v.setviewid(v.viewid+'_'+str(i))

    def update(self,):
        items = [v.update()['slots'][v.slot][0] for v in self.children]
        values = {'items': items}           
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result = {}
        result['slots'] = {self.slot:[item]}
        return result

    def get_items(self):
        pass
