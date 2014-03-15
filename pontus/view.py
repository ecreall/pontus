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

def merg_dicts(source, target):
    result = target
    for k in source.keys():
        if k in result.keys():
            if isinstance(result[k], list):
                result[k].extend(source[k])
            elif isinstance(result[k], dict):
                result[k] = merg_dicts(source[k], result[k])
        else:
            result[k] = source[k]
       
    return result

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
