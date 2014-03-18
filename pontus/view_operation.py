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
from pontus.wizard import STEPID
from pontus.form import FormView
from pontus.multipleview import MultipleView
from pontus.widget import SimpleFormWidget, AccordionWidget, SimpleMappingWidget, CheckboxChoiceWidget
from pontus.interfaces import IFormView
from pontus.resources import CallViewErrorPrincipalmessage, CallViewViewErrorCauses

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

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        ViewOperation.__init__(self, context, request, parent, wizard, index, **kwargs)
        if type(self.views).__name__ == 'function':
            self.views = self.views(self)


class MultipleContextsOperation(ViewOperation):
    view = default_view
    contexts = default_contexts

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
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

            subview.setviewid(subview.viewid+'_'+str(get_oid(item_context)))       
            self.children.append(subview)


class MultipleContextsViewsOperation(ViewOperation):
    views = None
    contexts = default_contexts

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        ViewOperation.__init__(self, context, request, parent, wizard, index, **kwargs)
        if type(self.views).__name__ == 'function':
            self.views = self.views(self)

        self.contexts = self.contexts()
    

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
    schema = EmptySchema(widget=SimpleFormWidget())
    widget = AccordionWidget()
    prefixe = 'All'

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
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

        self.schema.add_idnode(STEPID, str(self.index))
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

    self_template = 'pontus:templates/global_accordion.pt'

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        MultipleContextsOperation.__init__(self, context, request, parent, wizard, index, **kwargs)


    def update(self,):
        if not self.children:
            e = ViewError()
            e.principalmessage = CallViewErrorPrincipalmessage
            e.causes = CallViewViewErrorCauses
            raise e

        result = {}
        if isinstance(self.children[0], MultipleView):
            return self._updateMultipleview()

        views_result = []
        for v in self.children:
            try:
                view_result = v.update()
            except ViewError as e:
                continue

            if v.finished_successfully:
                self.finished_successfully = True

            if not isinstance(view_result, dict):
                return view_result
           
            views_result.append(view_result)
              
        items = [vr['coordiantes'][v.coordiantes][0] for vr in views_result]
        values = {'items': items, 'id':self.view.viewid}           
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordiantes'] = {self.coordiantes:[item]}
        for vr in views_result:
            vr.pop('coordiantes')
            merg_dicts(vr, result) #integrer les ressources

        return result

    def _updateMultipleview(self,):
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

            global_result = merg_dicts(view_result, global_result)
            for coordiante, values in view_result['coordiantes'].iteritems():
                item = {'view':v,'items': values, 'id': v.viewid}
                subbody = v.render_item(coordiantes='globalcoordiantes'+'_'+coordiante, item=item)
                item = {'view':v,'body': subbody, 'id': v.viewid+'_'+coordiante}
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

    #widgets
    items_widget = CheckboxChoiceWidget
    form_widget = SimpleFormWidget
    # a ne pas changer 
    schema = ItemsSchema

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        self.schema = self.schema(widget=self.form_widget())
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
        self.schema.add_idnode(STEPID, str(self.index))
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
