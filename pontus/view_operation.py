import re
import deform.widget
import colander
import itertools
from pyramid.httpexceptions import HTTPFound
from substanced.form import FormError
from substanced.util import get_oid

from dace.util import get_obj
from pontus.schema import Schema
from pontus.view import View
from pontus.form import FormView
from pontus.multipleview import MultipleView
from pontus.widget import SimpleFormWidget, AccordionWidget, SimpleMappingWidget, CheckboxChoiceWidget
from pontus.interfaces import IFormView


class ViewOperation(View):
    pass

class ViewsForContextOperation(ViewOperation):
    pass

def default_contexts(callview):
    return []


class ViewForContextsOperation(ViewOperation):
    view = None
    contexts = default_contexts

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        View.__init__(self, context, request, parent, wizard, index, **kwargs)
        self._init_children(self.contexts())


    def _init_children(self, contexts=None):
        if contexts is None:
            contexts = self.contexts()

        self.children = []
        if not isinstance(contexts, (list, tuple)):
            contexts = [contexts]

        for item_context in contexts:
            subview = self.view(item_context, self.request, self, None, None,**{})
            subview.setviewid(subview.viewid+'_'+str(get_oid(item_context)))       
            self.children.append(subview)



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


class CallFormView(FormView, ViewForContextsOperation):
    schema = EmptySchema(widget=SimpleFormWidget())
    widget = AccordionWidget()
    prefixe = 'All'

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        ViewForContextsOperation.__init__(self, context, request, parent, wizard, index, **kwargs)
        FormView.__init__(self, context, request, parent, wizard, index, **kwargs)
        self._addItemsNode()

    def _init_children(self, contexts):
        ViewForContextsOperation._init_children(self, contexts)
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
        self._setSchemaStepIndexNode()
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
                            views_context = self.children[v['context_oid']]
                            view_instance = None
                            for v_context in views_context:
                                if v_context.viewid == v['id']:
                                    view_instance = v_context
                                    break

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
                            self.esucces = True
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
       
            result['slots'] = {self.slot:[item]}
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


class CallView(ViewForContextsOperation):
    view = None
    merged = False
    self_template = 'pontus:templates/global_accordion.pt'

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        if hasattr(self.view, 'merged'):
            self.view.merged = self.merged

        ViewForContextsOperation.__init__(self, context, request, parent, wizard, index, **kwargs)


    def update(self,):
        result = {}
        if self.children and isinstance(self.children[0], MultipleView):
            return self._updateMultipleview()

        items = [v()['slots'][v.slot][0] for v in self.children]
        values = {'items': items, 'id':self.view.viewid}           
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['slots'] = {self.slot:[item]} #integrer les ressources
        return result

    def _updateMultipleview(self,):
        result = {}
        global_result = {}
        for v in self.children:
            view_result = v.update()
            if v.esucces:
                self.esucces = True

            if not isinstance(view_result, dict):
                return view_result

            global_result = v._merg(view_result, global_result)
            for slot, values in view_result['slots'].iteritems():
                item = {'view':v,'items': values, 'id': v.viewid}
                subbody = v.render_item(slot='globalslot'+'_'+slot, item=item)
                item = {'view':v,'body': subbody, 'id': v.viewid+'_'+slot}
                if slot in result:
                    result[slot].append(item) 
                else:
                    result[slot] = [item]

        for slot, items in result.iteritems():
            values = {'items': items, 'id':self.viewid+slot }           
            body = self.content(result=values, template=self.self_template)['body']
            item = self.adapt_item(body, self.viewid)
            global_result['slots'][slot]=[item]

        return  global_result 


class LoopSchema(Schema):
        items = colander.SchemaNode(
            colander.Set()
            )


class ExclusifCallViews(FormView):

    views = None
    contexts =  default_contexts
    items_widget = CheckboxChoiceWidget
    widget = SimpleFormWidget
    schema = LoopSchema

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        self.schema = self.schema(widget=self.widget())
        FormView.__init__(self, context, request, parent, wizard, index, **kwargs)
        self.items = self.contexts()
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
            viewforcontexts_class = CallView
            if IFormView.implementedBy(view):
                viewforcontexts_class = CallFormView

            viewforcontexts_class.title = view.title
            viewforcontexts_class.view = view
            view_instance = viewforcontexts_class(self.context, self.request, self.parent, self.wizard, self.index)
            self.children[key] = view_instance

    def _additemswidget(self):
        viewsschemanode =  self.schema.get('items')
        viewsschemanode.widget = self.get_itemswidget()

    def get_itemswidget(self):
        values = [(i, i.get_view(self.request)) for i in self.items]
        return self.items_widget(values=values, multiple=True)

    def _build_form(self):
        self.buttons = [b.title for b in self.views]
        return FormView._build_form(self)

    def update(self,):
        self._setSchemaStepIndexNode()
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
        elif posted_formid is not None:
            self.validated_items = [get_obj(int(o)) for o  in self.request.POST['__contextsoids__'].split(':')[1:]]
            viewname = self.request.POST['__viewid__']
            return self._call_callview(viewname)

        if item is None:
            item = self.show(form)

        if isinstance(item,dict):
            if error:
                item['isactive'] = True
       
            result['slots'] = {self.slot:[item]}
            result['js_links'] = reqts['js']
            result['css_links'] = reqts['css']
        else:
            result = item

        return result

    def _call_callview(self, viewname):
        callview = self.children[viewname]
        callview._init_children(self.validated_items)
        if IFormView.implementedBy(callview.view):
            self._addCallViewSchemaIdsNode(callview.schema, viewname)

        callview_result = callview()
        self.esucces = callview.esucces
        return callview_result

    def _getcontextsoids(self):
        result = ''
        for c in self.validated_items:
            result+= ':'+str(get_oid(c))

        return result

    def _addCallViewSchemaIdsNode(self, schema, viewname):
        if schema.get('__viewid__') is not None:
            schema.__delitem__('__viewid__') #return

        __viewid__ = colander.SchemaNode(
                colander.String(),
                name='__viewid__',
                widget=deform.widget.HiddenWidget(),
                default=viewname
                )
        schema.children.append(__viewid__)
        contextsoid = self._getcontextsoids()
        if schema.get('__contextsoids__') is not None:
            schema.__delitem__('__contextsoids__') #return

        __contextsoids__ = colander.SchemaNode(
                colander.String(),
                name='__contextsoids__',
                widget=deform.widget.HiddenWidget(),
                default=contextsoid
                )
        schema.children.append(__contextsoids__)

