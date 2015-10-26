# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

import colander
import deform
import deform.widget
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from dace.processinstance.core import Behavior, ValidationError
from dace.objectofcollaboration.runtime import Runtime
from dace.objectofcollaboration.object import Object
from dace.objectofcollaboration.services.processdef_container import (
    ProcessDefinitionContainer)

from pontus.view import BasicView
from pontus.form import FormView
from pontus.view_operation import MultipleView, MergedFormsView
from pontus.schema import select, Schema, omit
from pontus.widget import TableWidget, LineWidget



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

            return {}
        
        return {}

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


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
        body = self.content(args=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


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
            return {}

        return {}


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
        body = self.content(args=values, template=self.template)['body']
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
    renderer='pontus:templates/views_templates/grid.pt',
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
    renderer='pontus:templates/views_templates/grid.pt',
    )
class MergedFormsViewA(MergedFormsView):
    views = FormViewA
    title = 'MergedFormsView A'
    name = 'mergedformsviewa'
    contexts = get_item


class BehaviorC(Behavior):

    title = 'Behavior C'
    behavior_id = 'behaviorc'

    def start(self, context, request, appstruct, **kw):
        return {}

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


class SchemaB(Schema):
    
    title = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextInputWidget()
        )

    description = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextInputWidget()
        ) 


@view_config(
    name='formviewb',
    context=Runtime,
    renderer='pontus:templates/views_templates/grid.pt',
    )
class FormViewB(FormView):

    title = 'FormView B'
    schema = select(SchemaB(editable=True,omit=('title',)), [u'title', u'description'])
    behaviors = [BehaviorC]
    formid = 'formB'
    coordinates = 'left'

    def default_data(self):
        return self.context


class SchemaC(Schema):
    
    title = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextInputWidget()
        )

    description = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextInputWidget()
        )

    definitions = colander.SchemaNode(
        colander.Sequence(),
        omit(SchemaB(widget=LineWidget(), editable=True, name='definition'),['_csrf_token_']),
        widget=TableWidget(),
        title='Liste des definitions'
        )


@view_config(
    name='formviewc',
    context=ProcessDefinitionContainer,
    renderer='pontus:templates/views_templates/grid.pt',
    )
class FormViewC(FormView):

    title = 'FormView C'
    schema = select(SchemaC(factory=ProcessDefinitionContainer, editable=True,omit=((u'definitions',[u'title']),)), [u'title', u'description', (u'definitions',[u'title', u'description'])])
    behaviors = [BehaviorC]
    formid = 'formC'
    coordinates = 'left'

    def default_data(self):
        return self.context
