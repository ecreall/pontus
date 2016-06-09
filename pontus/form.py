# -*- coding: utf-8 -*-
# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

import os
from zope.interface import implementer
import deform.exception
import deform.widget
from deform.form import Button

from substanced.form import (
    FormView as SubstanceDFormView,
    FileUploadTempStore as FileUploadTempStoreOrigine,
    FormError)

from pontus.interfaces import IFormView
from pontus.view import ElementaryView
from pontus.util import merge_dicts
from pontus.default_behavior import Cancel
from pontus.schema import Schema


try:
    basestring
except NameError:
    basestring = str


def set_oid(children, formid):
    for child in children:
        child.oid = child.oid + formid
        if hasattr(child, 'children'):
            set_oid(child.children, formid)


@implementer(IFormView)
class FormView(ElementaryView, SubstanceDFormView):

    title = 'Form View'
    chmod = []
    schema = Schema()

    def __init__(self,
                 context,
                 request,
                 parent=None,
                 wizard=None,
                 stepid=None,
                 **kwargs):
        self.schema = self.schema.clone()
        SubstanceDFormView.__init__(self, context, request)
        ElementaryView.__init__(self, context, request, parent,
                                wizard, stepid, **kwargs)
        self.formid = kwargs.get('formid', getattr(self, 'formid', 'deform'))
        self.buttons = [Button(title=getattr(behavior,
                                            'submission_title',
                                            behavior.title),
                               name=behavior.title)
                        for behavior in self.behaviors_instances.values()]

    def _build_form(self):
        use_ajax = getattr(self, 'use_ajax', False)
        ajax_options = getattr(self, 'ajax_options', '{}')
        action = getattr(self, 'action', '')
        method = getattr(self, 'method', 'POST')
        formid = getattr(self, 'formid', 'deform')
        autocomplete = getattr(self, 'autocomplete', None)
        request = self.request
        bindings = self.bind()
        bindings.update({
            'request': request,
            'context': self.context,
            # see substanced.schema.CSRFToken
            '_csrf_token_': request.session.get_csrf_token()
            })
        self.schema = self.schema.bind(**bindings)
        form = self.form_class(self.schema, action=action, method=method,
                               buttons=self.buttons, formid=formid,
                               use_ajax=use_ajax, ajax_options=ajax_options,
                               autocomplete=autocomplete)
        # XXX override autocomplete; should be part of deform
        #form.widget.template = 'substanced:widget/templates/form.pt' 
        self.before(form)
        reqts = form.get_widget_resources()
        return form, reqts

    def setviewid(self, viewid):
        ElementaryView.setviewid(self, viewid)
        self.formid = viewid

    def get_view_requirements(self):
        bindings = self.bind()
        bindings.update({
            'request': self.request,
            'context': self.context,
            })
        schema = self.schema.bind(**bindings)
        reqts = self.form_class(schema).get_widget_resources()
        result = {}
        result['js_links'] = list(reqts['js'])
        result['css_links'] = list(reqts['css'])
        result = merge_dicts(self.requirements_copy, result)
        return result

    def has_id(self, id):
        formid = self.viewid + '_' + self.formid
        return formid == id

    def remove_tmp_stores(self, form):
        for store in getattr(form, 'stores', []):
            store.clear()

    def update(self,):
        self.init_stepid(self.schema)
        form, reqts = self._build_form()
        form.formid = self.viewid + '_' + form.formid
        set_oid(form.children, form.formid)
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
                        if (button.name in self.behaviors_instances) and \
                            isinstance(self.behaviors_instances[button.name],
                                       Cancel):
                            # bypass form validation for Cancel behavior
                            cancel_beh = self.behaviors_instances[button.name]
                            behaviors = self.behaviors_instances.values()
                            self.remove_tmp_stores(form)
                            cancel_beh.execute(self.context,
                                    self.request, {'behaviors': behaviors})
                            validated = {}
                        else:
                            controls = self.request.POST.items()
                            validated = form.validate(controls)

                    except deform.exception.ValidationFailure as e:
                        fail = getattr(self, '%s_failure' % button.title, None)
                        if fail is None:
                            fail = self._failure
                        item = fail(e, form)
                        error = True
                    else:
                        try:
                            behavior = self.behaviors_instances[button.name]
                            item = behavior.execute(self.context,
                                    self.request, validated)
                            self.finished_successfully = True
                            self.remove_tmp_stores(form)
                        except FormError as e:
                            snippet = '<div class="error">Failed: %s</div>' % e
                            self.request.sdiapi.flash(snippet, 'danger',
                                                      allow_duplicate=True)
                            item = self.adapt_item(form.render(validated),
                                                   form.formid)
                            error = True

                    break

        if item is None:
            if not self.finished_successfully:
                item = self.show(form)

        if isinstance(item, dict):
            if error:
                item['isactive'] = True

            result['coordinates'] = {self.coordinates: [item]}
            result['js_links'] = list(reqts['js'])
            result['css_links'] = list(reqts['css'])
            result = merge_dicts(self.requirements_copy, result)
        else:
            result = item

        return result

    def bind(self):
        return {}

    def before(self, form):
        if self.chmod:
            self._chmod(form, self.chmod)

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

    def _failure(self, e, form):
        return self.adapt_item(e.render(), form.formid)

    def _get(self, form, node):
        for child in form.children:
            if child.name == node:
                return child

        return None

    def _chmod(self, form, mask):
        for m in mask:
            node = self._get(form, m[0])
            if node is not None:
                if isinstance(m[1], basestring):
                    if m[1] == 'r':
                        node.widget.readonly = True
                else:
                    self._chmod(node.children[0], m[1])


class FileUploadTempStore(FileUploadTempStoreOrigine):

    def preview_url(self, uid):
        root = self.request.virtual_root
        return self.request.resource_url(
            root, '@@preview_image_upload', uid)

    def clear_item(self, uid):
        data = self.session.get('substanced.tempstore', {})
        value = data.pop(uid, None)
        if value:
            if 'randid' in value:
                randid = value['randid']
                fn = os.path.join(self.tempdir, randid)
                try:
                    os.remove(fn)
                except OSError:
                    pass

            if not data:
                self.session.pop('substanced.tempstore', {})
