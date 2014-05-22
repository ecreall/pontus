import colander
import deform
import deform.widget
from zope.interface import Interface
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from substanced.sdi import RIGHT

from pontus.view import BasicView
from pontus.form import FormView
from pontus.view_operation import MultipleView, MergedFormsView
from pontus.schema import select, Schema
from dace.processinstance.core import Behavior, ValidationError
from dace.objectofcollaboration.runtime import Runtime
from dace.objectofcollaboration.object import Object


class BehaviorAValidator(object):

    @classmethod
    def validate(cls, context, request, **kw):
        try:
            if not request.validationA:
                raise ValidationError()
        except AttributeError:
            if context.title.startswith('not'):
                raise ValidationError()
            else:
                return True
  
        return request.validationA


class BehaviorA(Behavior):

    title = 'Behavior A'
    behavior_id = 'behaviora'
 
    @classmethod
    def get_validator(cls, **kw):
        return BehaviorAValidator

    def start(self, context, request, appstruct, **kw):
        try:
            request.viewexecuted.append('behaviorA')
        except AttributeError:
            if 'title' in appstruct:
                context.title = appstruct['title']

            return True
        
        return True


class ViewA(BasicView):

    title = 'ViewA'
    template = 'pontus:tests/example/templates/testtemplate.pt'
    name = 'viewA'
    coordinates = 'left'
    behaviors = [BehaviorA]

    def update(self):
        self.execute(None)
        result = {} 
        values = {
                'title': self.title,
               }
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


class BehaviorBValidator(object):

    @classmethod
    def validate(cls, context, request, **kw):
        try:
            if not request.validationB:
                raise ValidationError()
        except AttributeError:
            return True

        return request.validationB


class BehaviorB(Behavior):

    title = 'Behavior B'
    behavior_id = 'behaviorb'
 
    @classmethod
    def get_validator(cls, **kw):
        return BehaviorBValidator

    def start(self, context, request, appstruct, **kw):
        try:
            request.viewexecuted.append('behaviorB')
        except AttributeError:
            return True

        return True


class ViewB(BasicView):

    title = 'ViewB'
    template = 'pontus:tests/example/templates/testtemplate.pt'
    name = 'viewB'
    coordinates = 'left'
    behaviors = [BehaviorB]

    def update(self):
        self.execute(None)
        result = {} 
        values = {
                'title': self.title,
               }
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


class MultipleViewA(MultipleView):
    title = 'MultipleView A'
    name = 'multipleviewa'
    views = (ViewA, ViewB)


class SchemaA(Schema):
    
    title = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextInputWidget()
        )

class FormViewA(FormView):

    title = 'FormView A'
    schema = select(SchemaA(), [u'title'])
    behaviors = [BehaviorA]
    formid = 'formA'
    coordinates = 'left'

    def default_data(self):
        return self.context 

@view_config(
    name='multipleformviewa',
    context=Runtime,
    renderer='pontus:templates/view.pt',
    )
class MultipleFromViewA(MultipleView):
    title = 'MultipleFormView A'
    name = 'multipleformviewa'
    views = (FormViewA, ViewB)


objectA = Object(title='objecta')
objectB = Object(title='objectb')

def get_item(view=None):
    return [objectA, objectB]

@view_config(
    name='mergedformsviewa',
    context=Runtime,
    renderer='pontus:templates/view.pt',
    )
class MergedFormsViewA(MergedFormsView):
    views = FormViewA
    title = 'MergedFormsView A'
    name = 'mergedformsviewa'
    contexts = get_item
