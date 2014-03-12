# -*- coding: utf-8 -*-
from zope.interface import implements
import deform.exception
import deform.widget
import colander
import itertools
from pyramid.httpexceptions import HTTPFound

from substanced.schema import Schema
from substanced.form import FormView as FV, FormError

from pontus.schema import Schema, omit
from pontus.wizard import Step, STEPID
from pontus.visual import VisualisableElement
from pontus.interfaces import IFormView
from pontus.view import View
from pontus.widget import TableWidget, LineWidget, SimpleFormWidget, AccordionWidget, SimpleMappingWidget
# Il faut partir de l'idée que toute est étape et non l'inverse.
# Une étape a une condition permettant de la validé. True par défaut



class FormView(View, FV):
    implements(IFormView)

    chmod = []

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        FV.__init__(self, context, request)
        View.__init__(self, context, request, parent, wizard, index)
        
    def _get(self, form, node):
        for child in form.children:
            if child.name == node:
                return child

        return None

    def _chmod(self, form, mask=[]):
        for m in mask:
            node = self._get(form, m[0])
            if node is not None:
                if isinstance(m[1], basestring):
                   if m[1] == u'r':
                       node.widget.readonly = True
                else:
                    self._chmod(node.children[0], m[1])

    def update(self,):
        self._setSchemaStepIndexNode()
        form, reqts = self._build_form()
        form.formid = self.viewid+'_'+form.formid
        item = None
        result = {}
        posted_formid = None
        if '__formid__' in self.request.POST:
            posted_formid = self.request.POST['__formid__']
 
        if posted_formid is not None and posted_formid == form.formid:
            for button in form.buttons:
                if button.name in self.request.POST:
                    success_method = getattr(self, '%s_success' % button.name)
                    try:
                        controls = self.request.POST.items()
                        validated = form.validate(controls)
                    except deform.exception.ValidationFailure as e:
                        fail = getattr(self, '%s_failure' % button.name, None)
                        if fail is None:
                            fail = self._failure
                        item = fail(e, form)
                    else:
                        try:
                            item = success_method(validated)
                            self.esucces = True
                        except FormError as e:
                            snippet = '<div class="error">Failed: %s</div>' % e
                            self.request.sdiapi.flash(snippet, 'danger',
                                                      allow_duplicate=True)
                            item =self.adapt_item(form.render(validated), form.formid)

                    break

        if item is None:
            item = self.show(form)

        if isinstance(item,dict):
            result['slots'] = {self.slot:[item]}
            result['js_links'] = reqts['js']
            result['css_links'] = reqts['css']
        else:
            result = item

        return result

    def before(self, form):
        if self.chmod:
            self._chmod(form, self.chmod)

    def _setSchemaStepIndexNode(self):
        if not (self.schema.children[len(self.schema.children)-1].name == STEPID):
            stepIndexNode = colander.SchemaNode(
                colander.String(),
                name = STEPID,
                widget=deform.widget.HiddenWidget(),
                default = str(self.index)
                )
            self.schema.children.append(stepIndexNode)
        else:
            self.schema.children[len(self.schema.children)-1].default = str(self.index)

    def _failure(self, e, form):
        return self.adapt_item(e.render(), form.formid)

    def show(self, form):
        result = self.default_data()
        body = None
        if result is None:
            body = form.render(readonly=False)
        else:
            body = form.render(appstruct=result, readonly=False)

        return self.adapt_item(body, form.formid)

    def default_data(self):
        return None 

    def setviewid(self, viewid):
        View.setviewid(self,viewid)
        self.formid = viewid


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

        for item_context in items:
            if item_context.title in self.children:
                self.children[item_context.title].append(self.view(item_context, request, self, None, None,**kwargs))
            else:
                self.children[item_context.title]=[self.view(item_context, request, self, None, None,**kwargs)]

        self._addItemsNode()
        views = list(itertools.chain.from_iterable([values for key, values in self.children.iteritems()]))

        for i, v in enumerate(views):
            v.setviewid(v.viewid+'_'+str(i))

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
                    else:
                        try:
                            item = success_method(validated)
                            self.esucces = True
                        except FormError as e:
                            snippet = '<div class="error">Failed: %s</div>' % e
                            self.request.sdiapi.flash(snippet, 'danger',
                                                      allow_duplicate=True)
                            item =self.adapt_item(form.render(validated), form.formid)

                    break

        if item is None:
            item = self.show(form)

        if isinstance(item,dict):
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

