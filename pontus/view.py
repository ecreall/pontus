import re
from zope.interface import implements
from zope.interface import providedBy

from pyramid.threadlocal import get_current_registry
from pyramid.interfaces import IView as IV, IViewClassifier
from pyramid import renderers
from pyramid.renderers import get_renderer
from pyramid.path import package_of
from pyramid_layout.layout import Structure

from substanced.util import get_oid

from pontus.interfaces import IView
from pontus.step import Step


class ViewError(Exception):
    principalmessage = ''
    causes = []
    solutions = []
    type = 'danger'
    template='templates/message.pt'

    

def merge_dicts(source, target):
    result = target
    for k in source.keys():
        if k in result.keys():
            if isinstance(result[k], list):
                result[k].extend(source[k])
            elif isinstance(result[k], dict):
                result[k] = merge_dicts(source[k], result[k])
        else:
            result[k] = source[k]
       
    return result

__emptytemplate__ = 'templates/empty.pt'

class View(Step):
    implements(IView)

    viewid = None
    title = 'View'
    coordinates = 'main' # default value
    item_template = 'templates/subview.pt'
    self_template = None

    def render_item(self, item, coordinates, parent):
        body = renderers.render(self.item_template, {'coordinates':coordinates,'subitem':item, 'parent': parent}, self.request)
        return Structure(body)

    def __init__(self, context, request, parent=None, wizard=None, index=None, **kwargs):
        Step.__init__(self, wizard, index)
        self.context = context
        self.request = request
        self.parent = parent
        if self.viewid is None:
            self.viewid = re.sub(r'\s', '_', self.title)

        if self.parent is not None:
            self.viewid = self.parent.viewid+'_'+self.viewid
        
        if self.context is not None:
            self.viewid = self.viewid+'_'+str(get_oid(self.context))

    def params(self, key=None):
        if key is None:
            return self.request.params

        if key in self.request.params:
            return self.request.params[key]

        return None

    @property
    def process(self):
        params = self.params('p_uid')    

    @property
    def action(self):
        pass

    
    def validate(self):
        return True

    def __call__(self):
        result = None
        try:
            self.validate()
            result = self.update()
        except ViewError as e:
            return self.failure(e)
            
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

    def failure(self, e, subject=None):#...
        content_message = renderers.render(e.template, {'error':e, 'subject': subject}, self.request)
        item =self.adapt_item('', self.viewid)
        item['messages'] = {e.type: [content_message]}
        item['isactive'] = True
        result = {'js_links': [], 'css_links': [], 'coordinates': {self.coordinates:[item]}}
        return result

class ElementaryView(View):
    pass
