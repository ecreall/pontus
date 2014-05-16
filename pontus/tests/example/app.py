from zope.interface import Interface
from pyramid.httpexceptions import HTTPFound
#from zope.authentication.interfaces import IAuthentication
#from zope.pluggableauth import PluggableAuthentication as PAU
#from com.ecreall.omegsi.library.authentication import initialize_pau

from pontus.view import BasicView
from pontus.view_operation import MultipleView
from dace.processinstance.core import Behavior, ValidationError


class BehaviorAValidator(object):

    @classmethod
    def validate(cls, context, request, **kw):
        if not request.validationA:
            raise ValidationError()

        return request.validationA


class BehaviorA(Behavior):

    title = 'Behavior A'
    behavior_id = 'behaviora'
 
    @classmethod
    def get_validator(cls, **kw):
        return BehaviorAValidator

    def start(self, context, request, appstruct, **kw):
        request.viewexecuted.append('behaviorA')
        return True


class ViewA(BasicView):

    title = 'ViewA'
    self_template = 'pontus:tests/example/templates/testtemplate.pt'
    name = 'viewA'
    coordinates = 'left'
    behaviors = [BehaviorA]

    def update(self):
        self.execute(None)
        result = {} 
        values = {
                'title': self.title,
               }
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


class BehaviorBValidator(object):

    @classmethod
    def validate(cls, context, request, **kw):
        if not request.validationB:
            raise ValidationError()

        return request.validationB


class BehaviorB(Behavior):

    title = 'Behavior B'
    behavior_id = 'behaviorb'
 
    @classmethod
    def get_validator(cls, **kw):
        return BehaviorBValidator

    def start(self, context, request, appstruct, **kw):
        request.viewexecuted.append('behaviorB')
        return True


class ViewB(BasicView):

    title = 'ViewB'
    self_template = 'pontus:tests/example/templates/testtemplate.pt'
    name = 'viewB'
    coordinates = 'left'
    behaviors = [BehaviorB]

    def update(self):
        self.execute(None)
        result = {} 
        values = {
                'title': self.title,
               }
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


class MultipleViewA(MultipleView):
    title = 'MultipleView A'
    name = 'multipleviewa'
    views = (ViewA, ViewB)

