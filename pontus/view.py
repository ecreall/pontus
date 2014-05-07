import json
import re

from zope.interface import implements
from zope.interface import providedBy

from pyramid.threadlocal import get_current_registry
from pyramid.interfaces import IView as IV, IViewClassifier
from pyramid import renderers
from pyramid.renderers import get_renderer
from pyramid.path import package_of
from pyramid_layout.layout import Structure
from pyramid.response import Response

from substanced.util import get_oid

from dace.processinstance.core import  ValidationError

from pontus.interfaces import IView
from pontus.core import Step


class ViewError(Exception):
    principalmessage = u""
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
    validators = []
    item_template = 'templates/subview.pt'
    self_template = None

    def render_item(self, item, coordinates, parent):
        body = renderers.render(self.item_template, {'coordinates':coordinates,'subitem':item, 'parent': parent}, self.request)
        return Structure(body)

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        super(View, self).__init__(wizard, stepid)
        self.context = context
        self.request = request
        self.parent = parent
        if self.viewid is None:
            self.viewid = re.sub(r'\s', '_', self.title).replace('\'','').replace('-','') #y a plus simple...expression reguliere

        if self.parent is not None:
            self.viewid = self.parent.viewid+'_'+self.viewid
        
        if self.context is not None:
            self.viewid = self.viewid+'_'+str(get_oid(self.context))

    def validate(self):
        for validator in self.validators:
            try:
                validator.validate(self.context, self.request)
            except ValidationError as e:
                raise ViewError()

        return True

    def params(self, key=None):
        if key is None:
            return self.request.params

        if key in self.request.params:
            return self.request.params[key]

        return None
  
    def before_update(self):
        pass

    def update(self):
        pass

    def after_update(self):
        pass

    def __call__(self):
        coordinates = self.params('coordinates')
        if coordinates is not None:
            self.coordinates = coordinates

        result = None
        try:
            self.validate()
            self.before_update()
            result = self.update()
            self.after_update()
        except ViewError as e:
            return self.failure(e)
            
        if isinstance(result, dict):
            if not ('js_links' in result):
                result['js_links'] = []

            if not ('css_links' in result):
                result['css_links'] = []

        return result

    def view_resources(self):
        pass

    def content(self, result, template=None, main_template=None):
        if template is None:
            template = self_template
            #registry = get_current_registry()
            #context_iface = providedBy(self.context)
            #view_deriver = registry.adapters.lookup((IViewClassifier, self.request.request_iface, context_iface), IV, name=self.title, default=None)
            #discriminator = view_deriver.__discriminator__().resolve()
            #template = registry.introspector.get('templates', discriminator).title

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

    def _get_message(self, e, subject=None):
        content_message = renderers.render(e.template, {'error':e, 'subject': subject}, self.request)
        return content_message

    def failure(self, e, subject=None):
        #TODO
        content_message = self. _get_message(e, subject)
        item =self.adapt_item('', self.viewid)
        item['messages'] = {e.type: [content_message]}
        item['isactive'] = True
        result = {'js_links': [], 'css_links': [], 'coordinates': {self.coordinates:[item]}}
        return result

    def success(self, validated=None):
        pass


class ElementaryView(View):

    behaviors = []
    validate_behaviors = True

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        super(ElementaryView, self).__init__(context, request, parent, wizard, stepid, **kwargs)
        self._allvalidators = list(self.validators)
        if self.validate_behaviors:
            self._allvalidators.extend([behavior.get_validator() for behavior in self.behaviors])

        self.init_behaviorinstances= []
        if 'behaviors' in kwargs:
            self.init_behaviorinstances = kwargs['behaviors']
    
        self.behaviorinstances = {}
        self._init_behaviors()

    def validate(self):
        for validator in self._allvalidators:
            try:
                validator.validate(self.context, self.request)
            except ValidationError as e:
                raise ViewError()

        return True

    def _init_behaviors(self):
        _behaviorinstances= {}
        for behavior in self.behaviors:
            try:
                behavior.get_validator().validate(self.context, self.request)
                behaviorinstance = behavior.get_instance(self.context, self.request)
                if behaviorinstance is not None:
                    key = behaviorinstance.__class__.__name__
                    _behaviorinstances[key] = behaviorinstance
            except ValidationError as e:
                continue

        for behaviorinstance in self.init_behaviorinstances:
                key = behaviorinstance.__class__.__name__
                _behaviorinstances[key] = behaviorinstance

        if _behaviorinstances:
            sorted_behaviors = _behaviorinstances.values()
            sorted_behaviors.sort()
            for behaviorinstance in sorted_behaviors:
                key = re.sub(r'\s', '_', behaviorinstance.title)
                self.behaviorinstances[key] = behaviorinstance
                try:
                    self.viewid = self.viewid+'_'+str(get_oid(behaviorinstance))
                except Exception:
                    continue

    def before_update(self):
        for behavior in self.behaviorinstances.values():
            behavior.before_execution(self.context, self.request)

    def execute(self, appstruct=None):
        for behavior in self.behaviorinstances.values():
            behavior.execute(self.context, self.request, appstruct)

    def after_update(self):
         pass
#        if self.finished_successfully:
#            for behavior in self.behaviorinstances.values():
#                behavior.after_execution(self.context, self.request)


class BasicView(ElementaryView):

    isexecutable = False
    
    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        super(BasicView, self).__init__(context, request, parent, wizard, stepid, **kwargs)
        self.finished_successfully = True
