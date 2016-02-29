# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

import re
from collections import OrderedDict
from webob.multidict import MultiDict
from zope.interface import implementer

from pyramid.view import view_config
import pyramid.httpexceptions as exc
from pyramid import renderers
from pyramid.renderers import get_renderer
from pyramid_layout.layout import Structure

from substanced.util import get_oid

from dace.processinstance.core import Error, ValidationError

from pontus.interfaces import IView
from pontus.core import Step
from pontus.util import copy_dict, update_resources
from pontus.resources import (
    BehaviorViewErrorPrincipalmessage,
    BehaviorViewErrorSolutions)
from pontus import _, log


class ViewError(Error):
    principalmessage = u""
    causes = []
    solutions = []
    type = 'danger'
    template = 'pontus:templates/views_templates/alert_message.pt'

    def render_message(self, request, subject=None):
        content_message = renderers.render(
            self.template,
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
    coordinates = 'main'# default value
    validators = []
    wrapper_template = 'templates/views_templates/view_wrapper.pt'
    template = None
    requirements = None
    css_class = "pontus-main-view"
    container_css_class = ""

    def render_item(self, item, coordinates, parent):
        body = renderers.render(
            self.wrapper_template,
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
            self.viewid = self.viewid + '_' + str(get_oid(self.context, ''))

        self._request_configuration()

    def _request_configuration(self):
        coordinates = self.params('coordinates')
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
        list_key = key + '[]'
        if list_key in self.request.params:
            islist = True

        if key in self.request.params or list_key in self.request.params:
            dict_copy = self.request.params.copy()
            dict_copy = MultiDict([(k.replace('[]', ''), value)
                                   for (k, value) in dict_copy.items()])
            while key in dict_copy:
                result.append(dict_copy.pop(key))

            len_result = len(result)
            if not islist and len_result == 1:
                return result[0]
            elif islist or len_result > 1:
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
        except ViewError as error:
            log.warning(error)
            raise error
        except Exception as http_error:
            log.exception(http_error)
            raise exc.HTTPInternalServerError()

        if isinstance(result, dict):
            if 'js_links' not in result:
                result['js_links'] = []

            if 'css_links' not in result:
                result['css_links'] = []

            update_resources(self.request, result)

        return result

    def content(self, args, template=None, main_template=None):
        if template is None:
            template = self.template

        if main_template is None:
            main_template = get_renderer(EMPTY_TEMPLATE).implementation()

        if isinstance(args, dict):
            args['main_template'] = main_template

        body = renderers.render(template, args, self.request)
        return {'body': body,
                'args': args}

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

    def failure(self, error, subject=None):
        error_body = error.render_message(self.request, subject)
        item = self.adapt_item('', self.viewid, True)
        item['messages'] = {error.type: [error_body]}
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
        self._all_validators = list(self.validators)
        self.specific_behaviors_instances = []
        self.behaviors_instances = OrderedDict()
        self.errors = []
        if 'behaviors' in kwargs:
            bis = kwargs['behaviors']
            self.specific_behaviors_instances = [bi for bi in bis
                                                 if bi._class_ in self.behaviors]

        specific_behaviors = [b._class_ for b in
                              self.specific_behaviors_instances]
        if self.validate_behaviors:
            self._all_validators.extend([behavior.get_validator()
                                         for behavior in self.behaviors
                                         if behavior not in specific_behaviors])

        self._init_behaviors(specific_behaviors)
        self.behaviors_instances = OrderedDict(
            sorted(self.behaviors_instances.items(),
                   key=lambda e:
                   self.behaviors.index(e[1].__class__)))

    def validate(self):
        try:
            for validator in self._all_validators:
                validator.validate(self.context, self.request)

            if self.validate_behaviors and self.specific_behaviors_instances:
                for init_v in self.specific_behaviors_instances:
                    init_v.validate(self.context, self.request)

        except ValidationError as error:
            view_error = ViewError()
            view_error.principalmessage = BehaviorViewErrorPrincipalmessage
            if error.principalmessage:
                view_error.causes = [error.principalmessage]

            view_error.solutions = BehaviorViewErrorSolutions
            raise view_error

        return True

    def _add_behaviorinstance(self, behaviorinstance):
        key = re.sub(r'\s', '_', behaviorinstance.title)
        self.behaviors_instances[key] = behaviorinstance
        try:
            self.viewid = self.viewid+'_'+str(get_oid(behaviorinstance))
        except Exception:
            pass

    def _init_behaviors(self, specific_behaviors):
        behaviors = [behavior for behavior in self.behaviors
                     if behavior not in specific_behaviors]
        for behavior in behaviors:
            try:
                wizard_behavior = None
                if self.wizard:
                    wizard_behavior = self.wizard.behaviorinstance

                behaviorinstance = behavior.get_instance(self.context,
                                                         self.request,
                                                         wizard=wizard_behavior)
                if behaviorinstance:
                    self._add_behaviorinstance(behaviorinstance)
            except ValidationError as error:
                self.errors.append(error)

        for behaviorinstance in self.specific_behaviors_instances:
            self._add_behaviorinstance(behaviorinstance)

    def before_update(self):
        for behavior in self.behaviors_instances.values():
            behavior.before_execution(self.context, self.request)

    def execute(self, appstruct=None):
        results = []
        for behavior in self.behaviors_instances.values():
            results.append(behavior.execute(
                self.context, self.request, appstruct))

        return results

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


@view_config(
    context=ViewError,
    renderer='pontus:templates/views_templates/grid.pt',
    )
class ViewErrorView(BasicView):
    title = _('An error has occurred!')
    name = 'viewerrorview'
    template = 'pontus:templates/views_templates/alert_message.pt'

    def update(self):
        self.title = self.request.localizer.translate(self.title)
        result = {}
        body = self.content(
            args={'error': self.context}, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates: [item]}
        return result
