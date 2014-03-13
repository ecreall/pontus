import deform.widget
import colander
import itertools
from pyramid.httpexceptions import HTTPFound

from pontus.schema import Schema
from pontus.view import View
from pontus.form import FormView
from pontus.multipleview import MultipleView
from pontus.widget import SimpleFormWidget, AccordionWidget, SimpleMappingWidget


class ViewSchema(Schema):
    id = colander.SchemaNode(
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


class CallFormView(FormView):
    schema = EmptySchema(widget=SimpleFormWidget())
    view = None
    widget = AccordionWidget()
    prefixe = 'All'

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        FormView.__init__(self, context, request, parent, wizard, index, **kwargs)
        self.children={}
        items = self.get_items()
        if not isinstance(items, (list, tuple)):
            items = [items]

        for i, item_context in enumerate(items):
            subform = self.view(item_context, request, self, None, None,**kwargs)
            subform.setviewid(subform.viewid+'_'+str(i))
            if item_context.title in self.children:
                self.children[item_context.title].append(subform)
            else:
                self.children[item_context.title]=[subform]

        self._addItemsNode()


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
        use_ajax = getattr(self, 'use_ajax', False)
        ajax_options = getattr(self, 'ajax_options', '{}')
        action = getattr(self, 'action', '')
        method = getattr(self, 'method', 'POST')
        formid = getattr(self, 'formid', 'deform')
        autocomplete = getattr(self, 'autocomplete', None)
        request = self.request
        self.schema = self.schema.bind(
            request=request,
            context=self.context,
            # see substanced.schema.CSRFToken
            _csrf_token_=request.session.get_csrf_token(), 
            )
        self.buttons = [b+' '+self.prefixe for b in self.view.buttons]
        form = self.form_class(self.schema, action=action, method=method,
                               buttons=self.buttons, formid=formid,
                               use_ajax=use_ajax, ajax_options=ajax_options,
                               autocomplete=autocomplete)
        # XXX override autocomplete; should be part of deform
        #form.widget.template = 'substanced:widget/templates/form.pt' 
        self.before(form)
        reqts = form.get_widget_resources()
        return form, reqts


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
                            views_context = self.children[v['title']]
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

    def get_items(self):
        pass

    def default_data(self):
        result = {'views':[]}
        views = list(itertools.chain.from_iterable([values for key, values in self.children.iteritems()]))
        for item in views:
            item_default_data = item.default_data()
            if item_default_data is None:
                item_default_data = {}
            item_default_data = {'item': item_default_data, 'id':item.viewid, 'title':item.context.title}
            result['views'].append(item_default_data)

        return result 


class CallView(View):
    view = None
    merged = False
    self_template = 'pontus:templates/global_accordion.pt'

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        View.__init__(self, context, request, parent, wizard, index, **kwargs)
        items = self.get_items()
        if hasattr(self.view, 'merged'):
            self.view.merged = self.merged

        if not isinstance(items, (list, tuple)):
            items = [items]

        self.children = []
        for i, item_context in enumerate(items):
            subview = self.view(item_context, request, self, None, None,**kwargs)
            subview.setviewid(subview.viewid+'_'+str(i))       
            self.children.append(subview)

    def update(self,):
        result = {}
        if self.children and isinstance(self.children[0], MultipleView):
            return self._updateMultipleview()

        items = [v.update()['slots'][v.slot][0] for v in self.children]
        values = {'items': items, 'id':v.viewid}           
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['slots'] = {self.slot:[item]}
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

    def get_items(self):
        pass
