import re
from collections import OrderedDict

from pyramid import renderers
from pyramid.renderers import get_renderer
from pyramid_layout.layout import Structure
from substanced.util import get_oid
from zope.interface import implementer

from dace.processinstance.core import  ValidationError

from pontus.interfaces import IView
from pontus.core import Step
from pontus.resources import (
                BehaviorViewErrorPrincipalmessage,
                BehaviorViewErrorCauses,
                BehaviorViewErrorSolutions)


class ViewError(Exception):
    principalmessage = u""
    causes = []
    solutions = []
    type = 'danger'
    template = 'templates/message.pt'


def merge_dicts(source, target):
    result = dict(target)
    for k in source.keys():
        if k in result.keys():
            if isinstance(result[k], list):
                result[k].extend(list(source[k]))
            elif isinstance(result[k], dict):
                result[k] = merge_dicts(source[k], result[k])
        else:
            if isinstance(source[k], list):
                result[k] = list(source[k])
            else:
                result[k] = source[k]

    return result


EMPTY_TEMPLATE = 'templates/empty.pt'

#TODO create decorator for pontus views
@implementer(IView)
class View(Step):
    """Abstract view"""

    viewid = None
    title = 'View'
    name = 'view'
    coordinates = 'main' # default value
    validators = []
    item_template = 'templates/subview.pt'
    template = None
    requirements = None

    def render_item(self, item, coordinates, parent):
        body = renderers.render(self.item_template,
                {'coordinates': coordinates,
                 'subitem': item,
                 'parent': parent}, self.request)
        return Structure(body)

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        super(View, self).__init__(wizard, stepid)
        self.context = context
        self.request = request
        self.parent = parent
        if self.viewid is None:
            self.viewid = self.name#re.sub(r'\s', '_', self.name).replace('\'','').replace('-','') #y a plus simple...expression reguliere

        if self.parent is not None:
            self.viewid = self.parent.viewid + '_' + self.viewid

        if self.context is not None:
            self.viewid = self.viewid + '_' + str(get_oid(self.context))

        self._request_configuration()

    def _request_configuration(self):
        coordinates = self.params('coordinates') #++
        if coordinates is not None:
            self.coordinates = coordinates

    @property
    def requirements_copy(self):
        if self.requirements is None:
            return {'css_links': [], 'js_links': []}
        else:
            copy = {}
            if 'css_links' in self.requirements:
                copy['css_links'] = list(self.requirements['css_links'])

            if 'js_links' in self.requirements:
                copy['js_links'] = list(self.requirements['js_links'])

            return copy

    def get_view_requirements(self):
        return self.requirements_copy

    def validate(self):
        for validator in self.validators:
            try:
                validator.validate(self.context, self.request)
            except ValidationError:
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

    def content(self, result, template=None, main_template=None):
        if template is None:
            template = self.template
            #registry = get_current_registry()
            #context_iface = providedBy(self.context)
            #view_deriver = registry.adapters.lookup((IViewClassifier, self.request.request_iface, context_iface), IV, name=self.title, default=None)
            #discriminator = view_deriver.__discriminator__().resolve()
            #template = registry.introspector.get('templates', discriminator).title

        if main_template is None:
            main_template = get_renderer(EMPTY_TEMPLATE).implementation()

        if isinstance(result, dict):
            result['main_template'] = main_template

        body = renderers.render(template, result, self.request)
        return {'body':body,
                'args':result,
               }

    def adapt_item(self, render, id, isactive=True):
        if self.parent is not None:
            isactive = False

        item = {'view': self, 'id': id, 'isactive': isactive}
        if isinstance(render, list):
            item['items'] = render
        else:
            item['body'] = render

        return item

    def setviewid(self, viewid):
        self.viewid = viewid

    def _get_message(self, e, subject=None):
        content_message = renderers.render(e.template,
                {'error': e, 'subject': subject}, self.request)
        return content_message

    def failure(self, e, subject=None):
        #TODO
        content_message = self. _get_message(e, subject)
        item = self.adapt_item('', self.viewid)
        item['messages'] = {e.type: [content_message]}
        item['isactive'] = True
        result = {'js_links': [], 'css_links': [],
                  'coordinates': {self.coordinates: [item]}}
        return result

    def success(self, validated=None):
        pass


class ElementaryView(View):
    """Abstract view"""

    behaviors = []
    validate_behaviors = True

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        super(ElementaryView, self).__init__(context, request, parent, wizard, stepid, **kwargs)
        self._allvalidators = list(self.validators)
        self.init_behaviorinstances= []
        if 'behaviors' in kwargs:
            bis = kwargs['behaviors']
            for bi in bis:
                if bi._class_ in self.behaviors:
                    self.init_behaviorinstances.append(bi)

        _init_behaviors = [b._class_ for b in self.init_behaviorinstances]
        if self.validate_behaviors:
            self._allvalidators.extend([behavior.get_validator() for behavior in self.behaviors if not (behavior in _init_behaviors)])

        self.behaviorinstances = OrderedDict()
        self._init_behaviors()

    def validate(self):
        try:
            for validator in self._allvalidators:
                validator.validate(self.context, self.request)

            if self.validate_behaviors and self.init_behaviorinstances:
                for init_v in self.init_behaviorinstances:
                    init_v.validate(self.context, self.request)

        except ValidationError as e:
            ve = ViewError()
            ve.principalmessage = BehaviorViewErrorPrincipalmessage
            ve.causes = [e.principalmessage]#BehaviorViewErrorCauses
            ve.solutions = BehaviorViewErrorSolutions
            raise ve

        return True

    def _init_behaviors(self):
        behavior_instances = OrderedDict()
        _init_behaviors = [b._class_ for b in self.init_behaviorinstances]
        self.errors = []
        for behavior in self.behaviors:
            if not (behavior in _init_behaviors):
                try:
                    wizard = None
                    if self.wizard is not None:
                        wizard = self.wizard.behaviorinstance

                    behaviorinstance = behavior.get_instance(self.context, self.request, wizard=wizard)
                    if behaviorinstance is not None:
                        key = behaviorinstance._class_.__name__
                        behavior_instances[key] = behaviorinstance
                except ValidationError as e:
                    self.errors.append(e)

        for behaviorinstance in self.init_behaviorinstances:
            key = behaviorinstance._class_.__name__
            behavior_instances[key] = behaviorinstance

        if behavior_instances:
            sorted_behaviors = behavior_instances.values()
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
    """Basic view"""

    isexecutable = False

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        super(BasicView, self).__init__(context, request, parent, wizard, stepid, **kwargs)
        self.finished_successfully = True

    def update(self):
        return {}
