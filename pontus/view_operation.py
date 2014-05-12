import re
import deform.widget
import colander
import itertools
from inspect import isfunction
from pyramid.httpexceptions import HTTPFound

from substanced.form import FormError
from substanced.util import get_oid

from dace.util import get_obj
from pontus.schema import Schema
from pontus.view import View, merge_dicts, ViewError
from pontus.form import FormView
from pontus.widget import (
        SimpleFormWidget, 
        AccordionWidget, 
        SimpleMappingWidget, 
        CheckboxChoiceWidget)
from pontus.interfaces import IFormView
from pontus.resources import (
        CallViewErrorPrincipalmessage, 
        CallViewViewErrorCauses, 
        MutltipleViewErrorPrincipalmessage, 
        MutltipleViewErrorCauses, 
        CallViewErrorCildrenNotValidatedmessage)
from pontus.core import STEPID, Step


def default_view(callview):
    return None


def default_views(callview):
    return []


def default_contexts(callview):
    return []


def default_context(callview):
    return callview.context


class ViewOperation(View):

    merged = False
    contexts = default_contexts
    views = default_views

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        super(ViewOperation, self).__init__(context, request, parent, wizard, stepid, **kwargs)
        if hasattr(self.views, '__func__'):
            self.views = self.views.__func__

        if type(self.views).__name__ == 'function':
            self.views = self.views(self)
        
        if not isinstance(self.views,(list, tuple, dict)):
            self.views = [self.views]

        self.contexts = self.contexts()


    def _request_configuration(self):
        super(ViewOperation, self)._request_configuration()
        tomerge = self.params('tomerge')
        if tomerge is not None:
            self.merged = bool(tomerge) 

    #l'operation renvoie une vue qui peut etre executable ou non. 
    #Il faut donc une fonction qui fixe si la vue renvoyee est executable ou non.
    def define_executable(self):
        return self.isexecutable


class MultipleViewsOperation(ViewOperation):
    pass


class MultipleContextsOperation(ViewOperation):

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        super(MultipleContextsOperation, self).__init__(context, request, parent, wizard, stepid, **kwargs)
        self.children = []
        self.children_notvalitaed = []
        self.allviews = []
        self.view = None
        if self.views:
            self.view = self.views[0]

        if self.view is not None:
            self._init_children(self.contexts)

    def _init_children(self, contexts=None):
        if contexts is None:
            contexts = self.contexts

        self.children = []
        if not isinstance(contexts, (list, tuple)):
            contexts = [contexts]

        for item_context in contexts:
            subview = self.view(item_context, self.request, self, self.wizard, self.stepid,**{})
            try:
                subview.validate()
            except ViewError as e:
                self.children_notvalitaed.append(item_context)
                continue

            self.children.append(subview)
            self.allviews.append(subview)

    def get_view_requirements(self):
        result = self.requirements_copy
        for view in self.children:
            view_requirements = view.get_view_requirements()
            result = merge_dicts(view_requirements, result)

        return result

class MultipleContextsViewsOperation(ViewOperation):
    pass
    

def default_builder(parent, views):
    if views is None:
        return

    for view in views:
        if isinstance(view, tuple):
            viewinstance = MultipleView(parent.context, parent.request, parent, parent.wizard, parent.stepid)
            viewinstance.merged = parent.merged
            if parent.merged:
                viewinstance.coordinates = parent.coordinates

            viewinstance.title = view[0]
            viewinstance.builder(view[1])
            if viewinstance.children:
                parent.children.append(viewinstance)
        else:
            viewinstance = view(parent.context, parent.request, parent, parent.wizard, parent.stepid)
            try:
                viewinstance.validate()
            except ViewError as e:
                continue

            if parent.merged:
                viewinstance.coordinates = parent.coordinates

            parent.children.append(viewinstance)        


class MultipleView(MultipleViewsOperation):
    
    title = 'Multiple View'
    builder = default_builder
    self_template = 'templates/submultipleview.pt'
    
    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        super(MultipleView, self).__init__(context, request, parent, wizard, stepid, **kwargs)
        self.children = []
        self._coordinates = []
        if self.views:
            self._init_views(self.views)

    def _init_views(self, views):
        self.builder(views)
        self.define_executable()

    def get_view_requirements(self):
        result = self.requirements_copy
        for view in self.children:
            view_requirements = view.get_view_requirements()
            result = merge_dicts(view_requirements, result)

        return result 

    def define_executable(self):
        _isexecutable =False
        for child in self.children:
            if child.isexecutable:
                _isexecutable = True
                break
       
        if not _isexecutable:
            self.isexecutable = False
            self.finished_successfully = True

        return self.isexecutable

    def _activate(self, items):
        if items:
            item = items[0]
            item['isactive'] = True
            if 'items' in item:
                self._activate(item['items'])

    def before_update(self):
        for view in self.children:
            view.before_update()
     
    def update(self,):
        #validation
        if not self.children:
            e = ViewError()
            e.principalmessage = MutltipleViewErrorPrincipalmessage
            e.causes = MutltipleViewErrorCauses
            raise e

        #faire l'update
        result = {}
        for view in self.children:
            try:
                view_result = view.update()
            except ViewError as e:
                continue

            if self.isexecutable and view.isexecutable and view.finished_successfully:
                self.finished_successfully = True
                return self.success(view_result)

            if not isinstance(view_result, dict):
                return view_result

            result = merge_dicts(view_result, result)

        if not result:
            e = ViewError()
            e.principalmessage = MutltipleViewErrorPrincipalmessage
            e.causes = MutltipleViewErrorCauses
            raise e

        for _coordinate in result['coordinates']:
            coordinate = _coordinate
            if self.merged:
                coordinate = self.coordinates

            items = result['coordinates'][coordinate]
            isactive = False
            for item in items:
                if item['isactive']:
                    isactive = True
                    break
            
            if not isactive:
                self._activate(items)
                if self.parent is None:
                    isactive = True

            _item = {'isactive':isactive,
                      'items': items,
                      'view': self,
                      'id':self.viewid}
            values = {'coordinates':coordinate,'subitem':_item, 'parent': self}
            body = self.content(result=values, template=self.self_template)['body']
            item = self.adapt_item(body, self.viewid)
            item['isactive'] = isactive
            result['coordinates'][coordinate] = [item]


        return result


    def adapt_item(self, render, id, isactive=True):
        item  = super(MultipleView, self).adapt_item(render, id, isactive)
        item['ismultipleview'] = True
        return item

    def after_update(self):
        if self.finished_successfully:
            for view in self.children:
                view.after_update()
        else:
            for view in self.children:
                if view.finished_successfully:
                    view.after_update()

    def failure(self, e, subject=None):#...
        content_message = self._get_message(e, subject)
        item =self.adapt_item([], self.viewid)
        item['messages'] = {e.type: [content_message]}
        item['isactive'] = True
        result = {'js_links': [], 'css_links': [], 'coordinates': {self.coordinates:[item]}}
        return result

    def success(self, validated=None):
        return validated


class ViewSchema(Schema):

    id = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.HiddenWidget()
                )

    context_oid = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.HiddenWidget()
                )

    title = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.HiddenWidget()
                )
   

class EmptySchema(Schema):
    views = colander.SchemaNode(
                colander.Sequence(),
                ViewSchema(name='view', widget=SimpleMappingWidget())
            )


class MergedFormsView(MultipleContextsOperation, FormView):
    title = 'MergedFormsView'
    schema = EmptySchema(widget=SimpleFormWidget())
    widget = AccordionWidget()
    suffixe = 'All'

    # Cette vue n'est pas un form par rapport a l'utilisateur: C'est une operation
    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        self.schema = self.schema.clone()
        super(MergedFormsView, self).__init__(context, request, parent, wizard, stepid, **kwargs)
        self.buttons = [b.title+' '+self.suffixe for b in self.view.behaviors]
        self._addItemsNode()

    def _init_children(self, contexts):
        MultipleContextsOperation._init_children(self, contexts)
        items = self.children
        self.children = {}
        for subform in items:
            context_oid = str(get_oid(subform.context))
            if context_oid in self.children:
                self.children[context_oid].append(subform)
            else:
                self.children[context_oid]=[subform]

    def _addItemsNode(self):
        if self.schema.get('views').children[0].get('item') is not None:
            self.schema.get('views').children[0].__delitem__('item') #return

        schema = self.view.schema.clone()
        schema.name = 'item'
        schema.widget = SimpleMappingWidget()
        viewsschemanode = self.schema.get('views')
        viewsschemanode.widget = self.widget
        viewsschemanode.children[0].children.append(schema)

    def before_update(self):
        for view in self.allviews:
            view.before_update()

    def update(self,):
        if not self.children:
            e = ViewError()
            e.principalmessage = CallViewErrorPrincipalmessage
            e.causes = CallViewViewErrorCauses
            raise e

        messages = {}
        if self.children_notvalitaed:
            e = ViewError()
            e.type = 'warning'
            e.principalmessage = CallViewErrorCildrenNotValidatedmessage
            e.causes = CallViewViewErrorCauses
            messages[e] = self._get_message(e)

        self.init_stepid(self.schema)
        form, reqts = self._build_form()
        form.formid = self.viewid+'_'+form.formid
        item = None
        result = {}
        posted_formid = None
        error = False
        if '__formid__' in self.request.POST:
            posted_formid = self.request.POST['__formid__']
 
        if posted_formid is not None and posted_formid == form.formid:
            for button in form.buttons:
                if button.name in self.request.POST:
                    try:
                        controls = self.request.POST.items()
                        validated = form.validate(controls)
                    except deform.exception.ValidationFailure as e:
                        #@TODO gestion des _failure des vues 
                        fail = getattr(self, '%s_failure' % button.name, None)
                        if fail is None:
                            fail = self._failure
                        item = fail(e, form)
                        error = True
                    else:
                        try:
                            #execution des vues postees (avec verification de la validite)  
                            views = validated['views']
                            for v in views:
                                views_context = None
                                if v['context_oid'] in self.children:
                                    views_context = self.children[v['context_oid']]
                                else:
                                    continue

                                view_instance = None
                                for v_context in views_context:
                                    if v_context.viewid == v['id']:
                                        view_instance = v_context
                                        break

                                if view_instance is None:
                                    continue

                                bname = button.name.replace(('_'+self.suffixe), '')
                                #dans le cas ou le behavior n'est pls valide: @TODO a voir
                                if bname in view_instance.behaviorinstances:
                                    behavior = view_instance.behaviorinstances[bname] 
                                    behavior.execute(self.context, self.request, v['item'])
                                    view_instance.finished_successfully = True

                            item = self.success(validated)
                            self.finished_successfully = True
                        except FormError as e:
                            snippet = '<div class="error">Failed: %s</div>' % e
                            self.request.sdiapi.flash(snippet, 'danger',
                                                      allow_duplicate=True)
                            item = self.adapt_item(form.render(validated), form.formid)
                            error = True

                    break

        if item is None:
            item = self.show(form)

        if isinstance(item,dict):
            if error:
                item['isactive'] = True

            if messages:
                item['messages']={}
                for e, messagecontent in messages.iteritems():
                    if e.type in item['messages']: 
                        item['messages'][e.type].append(messagecontent)
                    else:
                        item['messages'][e.type]=[messagecontent]
       
            result['coordinates'] = {self.view.coordinates:[item]}
            result['js_links'] = reqts['js']
            result['css_links'] = reqts['css']


        else:
            result = item

        return result

    def after_update(self):
        if self.finished_successfully:
            for view in self.allviews:
                view.after_update()

    def success(self, validated):
        return HTTPFound(
            self.request.mgmt_path(self.context, '@@contents'))#+self.request.view_name))

    def default_data(self):
        result = {'views':[]}
        views = list(itertools.chain.from_iterable([values for key, values in self.children.iteritems()]))
        for item in views:
            item_default_data = item.default_data()
            if item_default_data is None:
                item_default_data = {}
            item_default_data = {'item': item_default_data,
                                 'id': item.viewid,
                                 'context_oid':str(get_oid(item.context)), 
                                 'title':item.context.title}
            result['views'].append(item_default_data)

        return result 


class CallView(MultipleContextsOperation):

    title = 'CallView'
    self_template = 'pontus:templates/global_accordion.pt'

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        super(CallView, self).__init__(context, request, parent, wizard, stepid, **kwargs)
        self.define_executable()

    def define_executable(self):
        _isexecutable =False
        for child in self.children:
            if child.isexecutable:
                _isexecutable = True
                break
       
        if not _isexecutable:
            self.isexecutable = False
            self.finished_successfully = True

        return self.isexecutable

    def before_update(self):
        for view in self.children:
            view.before_update()

    def update(self,):
        if not self.children:
            e = ViewError()
            e.principalmessage = CallViewErrorPrincipalmessage
            e.causes = CallViewViewErrorCauses
            raise e

        result = {}
        global_result = {}
        for v in self.children:
            try:
                # c'est dans l'update que l'after et l'before sont executer dans l'update de la vue?
                view_result = v.update()
            except ViewError as e:
                continue

            if self.isexecutable and v.isexecutable and v.finished_successfully:
                self.finished_successfully = True
                return self.success(view_result)

            currentview = v
            if 'view' in view_result:
                currentview = view_result['view']

            global_result = merge_dicts(view_result, global_result)
            if len(view_result['coordinates']) == 1 and len(view_result['coordinates'].items()[0][1]) == 1:
                coordinate = view_result['coordinates'].items()[0][0]
                item = view_result['coordinates'].items()[0][1][0]
                if coordinate in result:
                    result[coordinate].append(item) 
                else:
                    result[coordinate] = [item]
            else:
                for coordinate, values in view_result['coordinates'].iteritems():
                    item = values[0]
                    subviewid = currentview.viewid+'_'+coordinate
                    item['id'] = subviewid
                    if coordinate in result:
                        result[coordinate].append(item) 
                    else:
                        result[coordinate] = [item]

        for coordinate, items in result.iteritems():
            values = {'items': items, 'id':self.viewid+coordinate }
            body = self.content(result=values, template=self.self_template)['body']
            item = self.adapt_item(body, self.viewid)
            global_result['coordinates'][coordinate]=[item]

        #if not (len(self.children) == len(self.contexts)):
        #    global_result['messages']
        return  global_result 

    def after_update(self):
        if self.finished_successfully:
            for view in self.children:
                view.before_update()
        else:
            for view in self.children:
                if view.finished_successfully:
                    view.before_update()

    def success(self, validated=None):
        return validated


class ItemsSchema(Schema):
        items = colander.SchemaNode(
            colander.Set()
            )


class CallSelectedContextsViews(FormView, MultipleContextsViewsOperation):

    title = 'CallSelectedContextsViews'
    #widgets
    items_widget = CheckboxChoiceWidget
    form_widget = SimpleFormWidget
    # a ne pas changer 
    schema = ItemsSchema

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        self.schema = self.schema(widget=self.form_widget())
        self.schema = self.schema.clone()
        super(CallSelectedContextsViews, self).__init__(context, request, parent, wizard, stepid, **kwargs)
        self.validated_items = []
        self.children = {}
        self._additemswidget()
        self._init_children()
        self.buttons = [b.title for b in self.views]

    def _init_children(self):
        _views = {}
        for v in self.views:
            name = re.sub(r'\s', '_', v.title)
            _views[name] = v

        for key, view in _views.iteritems():
            multiplecontextsview_class = CallView
            if IFormView.implementedBy(view):
                multiplecontextsview_class = MergedFormsView

            multiplecontextsview_class.title = view.title
            multiplecontextsview_class.views = view
            view_instance = multiplecontextsview_class(self.context, self.request, self.parent, self.wizard, self.stepid)
            self.children[key] = view_instance

    def _additemswidget(self):
        values = [(i, i.get_view(self.request)) for i in self.contexts]
        widget = self.items_widget(values=values, multiple=True)
        viewsschemanode =  self.schema.get('items')
        viewsschemanode.widget = widget

    def update(self,):
        if not self.contexts:
            e = ViewError()
            e.principalmessage = CallViewErrorPrincipalmessage
            e.causes = CallViewViewErrorCauses
            raise e

        self.init_stepid(self.schema)
        form, reqts = self._build_form()
        form.formid = self.viewid+'_'+form.formid
        item = None
        result = {}
        posted_formid = None
        error = False
        if '__formid__' in self.request.POST:
            posted_formid = self.request.POST['__formid__']
 
        if posted_formid is not None and posted_formid == form.formid:
            for button in form.buttons:
                if button.name in self.request.POST:
                    try:
                        controls = self.request.POST.items()
                        validated = form.validate(controls)
                        self.validated_items = [v for i, v  in enumerate(validated['items'])]
                    except deform.exception.ValidationFailure as e:
                        fail = getattr(self, '%s_failure' % button.name, None)
                        if fail is None:
                            fail = self._failure
                        item = fail(e, form)
                        error = True
                    else:
                        try:
                            item = self._call_callview(button.name)
                            return item
                        except FormError as e:
                            snippet = '<div class="error">Failed: %s</div>' % e
                            self.request.sdiapi.flash(snippet, 'danger',
                                                      allow_duplicate=True)
                            item = self.adapt_item(form.render(validated), form.formid)
                            error = True

                    break

        if posted_formid is not None and '__viewid__' in self.request.POST:
            posted_viewid= self.request.POST['__viewid__'].split(':')
            _viewid = posted_viewid[0]
            if _viewid == self.viewid:
                self.validated_items = [get_obj(int(o)) for o  in self.request.POST['__contextsoids__'].split(':')[1:]]
                if not self.validated_items:
                    e = ViewError()
                    e.principalmessage = CallViewErrorPrincipalmessage
                    e.causes = CallViewViewErrorCauses
                    raise e

                viewname = posted_viewid[1]
                return self._call_callview(viewname)

        if item is None:
            item = self.show(form)

        if isinstance(item,dict):
            if error:
                item['isactive'] = True
       
            result['coordinates'] = {self.coordinates:[item]}
            result['js_links'] = reqts['js']
            result['css_links'] = reqts['css']
        else:
            result = item

        return result

    def _call_callview(self, viewname):
        callview = self.children[viewname]
        callview._init_children(self.validated_items)
        callview.define_executable()
        if not callview.isexecutable:
            self.isexecutable = False
            self.finished_successfully = True

        if IFormView.implementedBy(callview.view):
            callview.schema.add_idnode('__viewid__', (self.viewid+':'+viewname))
            callview.schema.add_idnode('__contextsoids__', self._getcontextsoids())

        callview_result = callview()
        if self.isexecutable and callview.finished_successfully:
            self.finished_successfully = True
            return self.success(callview_result)

        return callview_result

    def _getcontextsoids(self):
        result = ''
        for c in self.validated_items:
            result+= ':'+str(get_oid(c))

        return result

    def success(self, validated=None):
        return validated


class Transition(object):

    def __init__(self, source, target, id, condition=(lambda x, y:True)):
        self.wizard = source.wizard
        self.source = source
        self.target = target
        self.source.add_outgoing(self)
        self.target.add_incoming(self)
        self.condition = condition
        self.id = id

    def validate(self):
        return self.condition(self.wizard.context, self.wizard.request)


class Wizard(MultipleViewsOperation):

    transitions = ()
    title = 'Wizard'
    durable = False # session ou pas?

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        super(Wizard, self).__init__(context, request, parent, wizard, stepid, **kwargs)
        self.transitionsinstances = {}
        self.viewsinstances = {}
        self.startnode = None
        self.endnode = None
        for key, view in self.views.iteritems():
            viewinstance = view(self.context, self.request, self, self, key)
            self.viewsinstances[key] = viewinstance

        for transition in self.transitions:
            sourceinstance = self.viewsinstances[transition[0]]
            targetinstance = self.viewsinstances[transition[1]]
            transitionid = transition[0]+'->'+transition[1]
            transitioninstance = Transition(sourceinstance, targetinstance, transitionid, transition[2])            
            self.transitionsinstances[transitionid] = transitioninstance

        self._add_startnode()
        self._add_endnode()
        self.currentsteps = [t.target for t in self.startnode._outgoing]

    def get_view_requirements(self):
        stepidkey = STEPID+self.viewid
        if stepidkey in self.request.session:
            self.currentsteps = [self.viewsinstances[self.request.session.pop(stepidkey)]]

        result = self.requirements_copy
        for view in self.currentsteps:
            view_requirements = view.get_view_requirements()
            result = merge_dicts(view_requirements, result)

        return result 

    def _add_startnode(self):
        initnodes = self._getinitnodes()
        self.startnode = Step(self,'start_'+self.viewid)
        for node in initnodes:
            transitionid = self.startnode.stepid+'->'+node.stepid
            self.transitionsinstances[transitionid] = Transition(self.startnode, node, transitionid)  

    def _add_endnode(self):
        finalnodes = self._getfinalnodes()
        self.endnode = Step(self,'end_'+self.viewid)
        for node in finalnodes:
            transitionid = node.stepid+'->'+self.endnode.stepid
            self.transitionsinstances[transitionid] = Transition(node, self.endnode, transitionid) 

    def _getinitnodes(self):
        result = []
        for view in self.viewsinstances.values():
            if not view._incoming:
                result.append(view)

        return result

    def _getfinalnodes(self):
        result = []
        for view in self.viewsinstances.values():
            if not view._outgoing:
                result.append(view)

        return result 

    def update(self):
        stepidkey = STEPID+self.viewid
        #TODO a voir
        #if stepidkey in self.request.POST:
        #    self.currentsteps = [self.viewsinstances[self.request.POST[stepidkey]]]

        if stepidkey in self.request.session:
            self.currentsteps = [self.viewsinstances[self.request.session.pop(stepidkey)]]
       
        result = None
        fs = False
        viewinstance, fs, result = self._get_result(self.currentsteps)
        if viewinstance is not None and fs and viewinstance._outgoing and not(viewinstance._outgoing[0].target == self.endnode):
            viewinstance.after_update()
            nextsteps = [transition.target for transition in viewinstance._outgoing if transition.validate()]
            viewinstance, fs, result = self._get_result(nextsteps)

        if fs and (viewinstance._outgoing[0].target == self.endnode):
            self.finished_successfully = True
            viewinstance.after_update()
            self.request.session.__delitem__(stepidkey)
            if viewinstance.isexecutable:
                return self.success()

            return result

        return result

    def _get_result(self, sourceviews):
        result = None
        if len(sourceviews) == 1:
            viewinstance = sourceviews[0]
            viewinstance.before_update()
            result = viewinstance.update()
            self.title = viewinstance.title
            if isinstance(result,dict):
                result['view'] = viewinstance

            return viewinstance, viewinstance.finished_successfully, result
        else:
            multipleviewinstance = MultipleView(self.context, self.request, self, self)
            multipleviewinstance.views = sourceviews
            viewinstance.before_update()
            result = multipleviewinstance.update()
            viewinstance = None
            for v in sourceviews:
                if v.finished_successfully:
                    viewinstance = v

            if isinstance(result,dict):
                result['view'] = viewinstance

            return viewinstance, multipleviewinstance.finished_successfully, result

    def success(self, validated=None):
        return HTTPFound(
            self.request.mgmt_path(self.context, '@@index'))
        
