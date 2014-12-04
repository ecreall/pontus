# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

import re
from collections import OrderedDict
from webob.multidict import MultiDict

from pyramid import renderers
from pyramid.renderers import get_renderer
from pyramid_layout.layout import Structure
from substanced.util import get_oid
from zope.interface import implementer

from dace.processinstance.core import  Error, ValidationError

from pontus.interfaces import IView
from pontus.core import Step
from pontus.util import copy_dict
from pontus.resources import (
                BehaviorViewErrorPrincipalmessage,
                BehaviorViewErrorSolutions)
from pontus import _


class ViewError(Error):
    principalmessage = u""
    causes = []
    solutions = []
    type = 'danger'
    template = 'pontus:templates/views_templates/alert_message.pt'

    def render_message(self, request, subject=None):
        content_message = renderers.render(self.template,
                {'error': self, 'subject': subject}, request)
        return content_message


EMPTY_TEMPLATE = 'templates/views_templates/empty.pt'


@implementer(IView)
class View(Step):
    """Abstract view"""

    viewid = None
    title = _('View')
    description = ""
    name = 'view'
    coordinates = 'main' # default value
    validators = []
    wrapper_template = 'templates/views_templates/view_wrapper.pt'
    template = None
    requirements = None
    css_class = "pontus-main-view"

    def render_item(self, item, coordinates, parent):
        body = renderers.render(self.wrapper_template,
                {'coordinates': coordinates,
                 'subitem': item,
                 'parent': parent}, self.request)
        return Structure(body)

    def __init__(self, 
                 context, 
                 request, 
                 parent=None, 
                 wizard=None, 
                 stepid=None, 
                 **kwargs):
        super(View, self).__init__(wizard, stepid)
        self.context = context
        self.request = request
        self.parent = parent
        if self.viewid is None:
            self.viewid = self.name

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
            return copy_dict(self.requirements)

    def has_id(self, id):
        return self.viewid == id

    def get_view_requirements(self):
        return self.requirements_copy

    def validate(self):
        for validator in self.validators:
            try:
                validator.validate(self.context, self.request)
            except ValidationError as error:
                view_error = ViewError()
                view_error.principalmessage = BehaviorViewErrorPrincipalmessage
                if getattr(error, 'principalmessage', ''):
                    view_error.causes = [error.principalmessage]

                view_error.solutions = BehaviorViewErrorSolutions
                raise view_error

        return True

    def params(self, key=None):
        result = []
        if key is None:
            return self.request.params

        islist = False
        if (key+'[]') in self.request.params:
            islist = True

        if key in self.request.params or (key+'[]') in self.request.params:
            dict_copy = self.request.params.copy()
            dict_copy = MultiDict([(k.replace('[]', ''), value) \
                                   for (k, value) in dict_copy.items()])
            try:
                while True:
                    result.append(dict_copy.pop(key))
            except Exception:
                if len(result) == 1 and not islist:
                    return result[0]
                elif len(result) > 1 or islist:
                    return result

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

    def failure(self, e, subject=None):
        error_body = e.render_message(self.request, subject)
        item = self.adapt_item('', self.viewid, True)
        item['messages'] = {e.type: [error_body]}
        result = {'js_links': [], 
                  'css_links': [],
                  'coordinates': {self.coordinates: [item]}}
        return result

    def success(self, validated=None):
        pass


class ElementaryView(View):
    """Abstract view"""

    behaviors = []
    validate_behaviors = True

    def __init__(self, 
                 context, 
                 request, 
                 parent=None, 
                 wizard=None, 
                 stepid=None, 
                 **kwargs):
        super(ElementaryView, self).__init__(context, request, parent, 
                                             wizard, stepid, **kwargs)
        self._allvalidators = list(self.validators)
        self.init_behaviorinstances = []
        if 'behaviors' in kwargs:
            bis = kwargs['behaviors']
            self.init_behaviorinstances = [bi for bi in bis \
                                           if bi._class_ in self.behaviors]

        _init_behaviors = [b._class_ for b in self.init_behaviorinstances]
        if self.validate_behaviors:
            self._allvalidators.extend([behavior.get_validator() \
                                        for behavior in self.behaviors \
                                        if not (behavior in _init_behaviors)])

        self.behaviorinstances = OrderedDict()
        self._init_behaviors(_init_behaviors)

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
            if e.principalmessage:
                ve.causes = [e.principalmessage]

            ve.solutions = BehaviorViewErrorSolutions
            raise ve

        return True

    def _init_behaviors(self, init_behaviors):
        behavior_instances = OrderedDict()
        self.errors = []
        for behavior in self.behaviors:
            if not (behavior in init_behaviors):
                try:
                    wizard = None
                    if self.wizard is not None:
                        wizard = self.wizard.behaviorinstance

                    behaviorinstance = behavior.get_instance(self.context, 
                                                             self.request, 
                                                             wizard=wizard)
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


class BasicView(ElementaryView):
    """Basic view"""

    isexecutable = False

    def __init__(self, 
                 context, 
                 request, 
                 parent=None, 
                 wizard=None, 
                 stepid=None, 
                 **kwargs):
        super(BasicView, self).__init__(context, request, parent, 
                                        wizard, stepid, **kwargs)
        self.finished_successfully = True

    def update(self):
        return {}
