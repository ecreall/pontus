import re
import deform.widget
import colander
import itertools
from pyramid.httpexceptions import HTTPFound

from substanced.form import FormError
from substanced.util import get_oid

from dace.util import get_obj
from pontus.schema import Schema
from pontus.view import View, merg_dicts, ViewError
from pontus.form import FormView
from pontus.widget import SimpleFormWidget, AccordionWidget, SimpleMappingWidget, CheckboxChoiceWidget
from pontus.interfaces import IFormView
from pontus.resources import CallViewErrorPrincipalmessage, CallViewViewErrorCauses, MutltipleViewErrorPrincipalmessage, MutltipleViewErrorCauses
from pontus.step import STEPID, Transition, Step


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


class MultipleViewsOperation(ViewOperation):
    views = default_views

    def __init__(self, context, request, parent=None, wizard=None, index=None, **kwargs):
        ViewOperation.__init__(self, context, request, parent, wizard, index, **kwargs)
        if type(self.views).__name__ == 'function':
            self.views = self.views(self)


class MultipleContextsOperation(ViewOperation):
    view = default_view
    contexts = default_contexts

    def __init__(self, context, request, parent=None, wizard=None, index=None, **kwargs):
        ViewOperation.__init__(self, context, request, parent, wizard, index, **kwargs)
        if type(self.view).__name__ == 'function':
            self.view = self.view(self)

        self.contexts = self.contexts()
        self._init_children(self.contexts)


    def _init_children(self, contexts=None):
        if contexts is None:
            contexts = self.contexts

        self.children = []
        if not isinstance(contexts, (list, tuple)):
            contexts = [contexts]

        for item_context in contexts:
            subview = self.view(item_context, self.request, self, self.wizard, self.index,**{})
            try:
                subview.validate()
            except ViewError as e:
                continue

            self.children.append(subview)


class MultipleContextsViewsOperation(ViewOperation):
    views = None
    contexts = default_contexts

    def __init__(self, context, request, parent=None, wizard=None, index=None, **kwargs):
        ViewOperation.__init__(self, context, request, parent, wizard, index, **kwargs)
        if type(self.views).__name__ == 'function':
            self.views = self.views(self)

        self.contexts = self.contexts()
    


def default_builder(parent, views):
    if views is None:
        return

    for view in views:
        if isinstance(view, tuple):
            viewinstance = MultipleView(parent.context, parent.request, parent, parent.wizard, parent.index)
            viewinstance.merged = parent.merged
            if parent.merged:
                viewinstance.coordiantes = parent.coordiantes

            viewinstance.title = view[0]
            viewinstance.builder(view[1])
            if viewinstance.children:
                parent.children.append(viewinstance)
        else:
            viewinstance = view(parent.context, parent.request, parent, parent.wizard, parent.index)
            try:
                viewinstance.validate()
            except ViewError as e:
                continue

            if parent.merged:
                viewinstance.coordiantes = parent.coordiantes

            parent.children.append(viewinstance)        


class MultipleView(View):
    
    title = 'Multiple View'
    views = ()
    builder = default_builder
    merged = False
    item_template = 'templates/submultipleview.pt'
    self_template = 'templates/submultipleview.pt'
    
    def __init__(self, context, request, parent=None, wizard=None, index=None):
        super(MultipleView, self).__init__(context, request, parent, wizard, index)
        self.children = []
        self._coordiantes = []
        self.builder(self.views)

    def _activate(self, items):
        if items:
            item = items[0]
            item['isactive'] = True
            if 'items' in item:
                self._activate(item['items'])

    def update(self,):
        if not self.children:
            e = ViewError()
            e.principalmessage = MutltipleViewErrorPrincipalmessage
            e.causes = MutltipleViewErrorCauses
            raise e

        result = {}
        for view in self.children:
            try:
                view_result = view.update()
            except ViewError as e:
                continue

            if view.finished_successfully:
                self.finished_successfully = True

            if not isinstance(view_result,dict):
                return view_result

            result = merg_dicts(view_result, result)

        if not result:
            return None

        for coordiante in result['coordiantes']:
            items = result['coordiantes'][coordiante]
            isactive = False
            for item in items:
                if item['isactive']:
                    isactive = True
                    break
            
            if not isactive:
                self._activate(items)
                if self.parent is None:
                    isactive = True

            result['coordiantes'][coordiante] = [{'isactive':isactive,
                                      'items': items,
                                      'view': self,
                                      'id':self.viewid}]

        return result

    def failure(self, e, subject=None):#...
        content_message = renderers.render(e.template, {'error':e, 'subject': subject}, self.request)
        item =self.adapt_item([], self.viewid)
        item['messages'] = {e.type: [content_message]}
        item['isactive'] = True
        result = {'js_links': [], 'css_links': [], 'coordiantes': {self.coordiantes:[item]}}
        return result


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


class CallFormView(FormView, MultipleContextsOperation):
    title = 'CallFormView'
    schema = EmptySchema(widget=SimpleFormWidget())
    widget = AccordionWidget()
    prefixe = 'All'

    def __init__(self, context, request, parent=None, wizard=None, index=None, **kwargs):
        self.schema = self.schema.clone()
        MultipleContextsOperation.__init__(self, context, request, parent, wizard, index, **kwargs)
        FormView.__init__(self, context, request, parent, wizard, index, **kwargs)
        self._addItemsNode()

    def _init_children(self, contexts):
        MultipleContextsOperation._init_children(self, contexts)
        items = self.children
        self.children = {}
        for i, subform in enumerate(items):
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

    def _build_form(self):
        self.buttons = [b+' '+self.prefixe for b in self.view.buttons]
        return FormView._build_form(self)


    def update(self,):
        if not self.children:
            e = ViewError()
            e.principalmessage = CallViewErrorPrincipalmessage
            e.causes = CallViewViewErrorCauses
            raise e

        self.init_stepindex(self.schema)
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
                    success_method = getattr(self, 'success' )
                    try:
                        controls = self.request.POST.items()
                        validated = form.validate(controls)
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

                            bname = button.name.replace(('_'+self.prefixe), '')

                            view_success_method = getattr(view_instance, '%s_success' % bname )
                            view_success_method(v['item'])

                    except deform.exception.ValidationFailure as e:
                        fail = getattr(self, '%s_failure' % button.name, None)
                        if fail is None:
                            fail = self._failure
                        item = fail(e, form)
                        error = True
                    else:
                        try:
                            item = success_method(validated)
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
       
            result['coordiantes'] = {self.view.coordiantes:[item]}
            result['js_links'] = reqts['js']
            result['css_links'] = reqts['css']
        else:
            result = item

        return result

    def success(self, validated):
        return HTTPFound(
            self.request.mgmt_path(self.context, '@@'+self.request.view_name))

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

    def __init__(self, context, request, parent=None, wizard=None, index=None, **kwargs):
        MultipleContextsOperation.__init__(self, context, request, parent, wizard, index, **kwargs)

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
                view_result = v.update()
            except ViewError as e:
                continue

            if v.finished_successfully:
                self.finished_successfully = True

            if not isinstance(view_result, dict):
                return view_result

            currentview = v
            if 'view' in view_result:
                currentview = view_result['view']

            global_result = merg_dicts(view_result, global_result)
            if len(view_result['coordiantes']) == 1 and len(view_result['coordiantes'].items()[0][1]) == 1:
                coordiante = view_result['coordiantes'].items()[0][0]
                item = view_result['coordiantes'].items()[0][1][0]
                if coordiante in result:
                    result[coordiante].append(item) 
                else:
                    result[coordiante] = [item]
            else:
                for coordiante, values in view_result['coordiantes'].iteritems():
                    subviewid = currentview.viewid+'_'+coordiante
                    item = {'view':currentview,'items': values, 'id': subviewid}
                    subbody = currentview.render_item(coordiantes='globalcoordiantes'+'_'+coordiante, item=item, parent=None)
                    item = {'view':currentview,'body': subbody, 'id':subviewid }
                    if coordiante in result:
                        result[coordiante].append(item) 
                    else:
                        result[coordiante] = [item]

        for coordiante, items in result.iteritems():
            values = {'items': items, 'id':self.viewid+coordiante }           
            body = self.content(result=values, template=self.self_template)['body']
            item = self.adapt_item(body, self.viewid)
            global_result['coordiantes'][coordiante]=[item]

        #if not (len(self.children) == len(self.contexts)):
        #    global_result['messages']

        return  global_result 


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

    def __init__(self, context, request, parent=None, wizard=None, index=None, **kwargs):
        self.schema = self.schema(widget=self.form_widget())
        self.schema = self.schema.clone()
        FormView.__init__(self, context, request, parent, wizard, index, **kwargs)
        MultipleContextsViewsOperation.__init__(self, context, request, parent, wizard, index, **kwargs)
        self.validated_items = []
        self.children = {}
        self._additemswidget()
        self._init_children()

    def _init_children(self):
        _views = {}
        for v in self.views:
            name = re.sub(r'\s', '_', v.title)
            _views[name] = v

        for key, view in _views.iteritems():
            multiplecontextsview_class = CallView
            if IFormView.implementedBy(view):
                multiplecontextsview_class = CallFormView

            multiplecontextsview_class.title = view.title
            multiplecontextsview_class.view = view
            view_instance = multiplecontextsview_class(self.context, self.request, self.parent, self.wizard, self.index)
            self.children[key] = view_instance

    def _additemswidget(self):
        values = [(i, i.get_view(self.request)) for i in self.contexts]
        widget = self.items_widget(values=values, multiple=True)
        viewsschemanode =  self.schema.get('items')
        viewsschemanode.widget = widget

    def _build_form(self):
        self.buttons = [b.title for b in self.views]
        return FormView._build_form(self)

    def update(self,):
        self.init_stepindex(self.schema)
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
                    success_method = getattr(self, '_call_callview' )
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
                            item = success_method(button.name)
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
                viewname = posted_viewid[1]
                return self._call_callview(viewname)

        if item is None:
            item = self.show(form)

        if isinstance(item,dict):
            if error:
                item['isactive'] = True
       
            result['coordiantes'] = {self.coordiantes:[item]}
            result['js_links'] = reqts['js']
            result['css_links'] = reqts['css']
        else:
            result = item

        return result

    def _call_callview(self, viewname):
        callview = self.children[viewname]
        callview._init_children(self.validated_items)
        if IFormView.implementedBy(callview.view):
            callview.schema.add_idnode('__viewid__', (self.viewid+':'+viewname))
            callview.schema.add_idnode('__contextsoids__', self._getcontextsoids())

        callview_result = callview()
        self.finished_successfully = callview.finished_successfully
        return callview_result

    def _getcontextsoids(self):
        result = ''
        for c in self.validated_items:
            result+= ':'+str(get_oid(c))

        return result


class Wizard(MultipleViewsOperation):

    transitions = ()
    title = 'Wizard'

    def __init__(self, context, request, parent=None, wizard=None, index='', **kwargs):
        MultipleViewsOperation.__init__(self, context, request, parent, wizard, index, **kwargs)
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


    def _add_startnode(self):
        initnodes = self._getinitnodes()
        self.startnode = Step(self,'start_'+self.viewid)
        for node in initnodes:
            transitionid = self.startnode.index+'->'+node.index
            self.transitionsinstances[transitionid] = Transition(self.startnode, node, transitionid)  

    def _add_endnode(self):
        finalnodes = self._getfinalnodes()
        self.endnode = Step(self,'end_'+self.viewid)
        for node in finalnodes:
            transitionid = node.index+'->'+self.endnode.index
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
        if stepidkey in self.request.POST:
            self.currentsteps = [self.viewsinstances[self.request.POST[stepidkey]]]

        result = None
        fs = False
        viewinstance, fs, result = self._get_result(self.currentsteps)
        if viewinstance is not None and fs and viewinstance._outgoing and not(viewinstance._outgoing[0].target == self.endnode) :
            nextsteps = [transition.target for transition in viewinstance._outgoing if transition.validate()]
            v, fs, result = self._get_result(nextsteps)

        self.finished_successfully = fs
        return result

    def _get_result(self, sourceviews):
        result = None
        if len(sourceviews) == 1:
            viewinstance = sourceviews[0]
            result = viewinstance.update()
            self.title = viewinstance.title
            if isinstance(result,dict):
                result['view'] = viewinstance

            return viewinstance, viewinstance.finished_successfully, result
        else:
            multipleviewinstance = MultipleView(self.context, self.request, self, self)
            multipleviewinstance.views = sourceviews
            result = multipleviewinstance.update()
            viewinstance = None
            for v in sourceviews:
                if v.finished_successfully:
                    viewinstance = v

            if isinstance(result,dict):
                result['view'] = viewinstance

            return viewinstance, multipleviewinstance.finished_successfully, result
        
        
