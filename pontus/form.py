# -*- coding: utf-8 -*-
from pyramid.httpexceptions import HTTPFound
from zope.interface import implements
import deform.exception
import deform.widget
import colander

from substanced.form import FormView as FV, FormError

from pontus.interfaces import IFormView
from pontus.view import ElementaryView, ViewError, merge_dicts
from pontus.resources import CallViewErrorPrincipalmessage, CallViewViewErrorCauses



class FormView(ElementaryView, FV):
    implements(IFormView)

    title = 'Form View'
    chmod = []

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        self.schema = self.schema.clone()
        FV.__init__(self, context, request)
        ElementaryView.__init__(self, context, request, parent, wizard, stepid, **kwargs)
        self.buttons = [behavior.title for behavior in self.behaviorinstances.values()]
        
    def setviewid(self, viewid):
        View.setviewid(self,viewid)
        self.formid = viewid

    def get_view_requirements(self):
        form, reqts = self._build_form()
        result = {}
        result['js_links'] = list(reqts['js'])
        result['css_links'] = list(reqts['css'])
        _requirements = self.requirements_copy
        result = merge_dicts(_requirements, result)
        return result
        
    def update(self,):
        #if not self.buttons:
        #    e = ViewError()
        #    e.principalmessage = CallViewErrorPrincipalmessage
        #    e.causes = CallViewViewErrorCauses
        #    raise e
        self.init_stepid(self.schema) # dans le before_update?!
        form, reqts = self._build_form()
        form.formid = self.viewid+'_'+form.formid
        for c in form.children:
            c.oid = c.oid+form.formid
 
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
                        fail = getattr(self, '%s_failure' % button.name, None)
                        if fail is None:
                            fail = self._failure
                        item = fail(e, form)
                        error = True
                    else:
                        try:
                            behavior = self.behaviorinstances[button.name]
                            item = behavior.execute(self.context, self.request, validated)
                            self.finished_successfully = True
                        except FormError as e:
                            snippet = '<div class="error">Failed: %s</div>' % e
                            self.request.sdiapi.flash(snippet, 'danger',
                                                      allow_duplicate=True)
                            item = self.adapt_item(form.render(validated), form.formid)
                            error = True

                    break

        if item is None:
            if not self.finished_successfully:
                item = self.show(form)
            else:
                item = HTTPFound(self.request.mgmt_path(self.context, '@@index'))

        if isinstance(item,dict):
            if error:
                item['isactive'] = True

            if self.wizard is not None: # changer pour un truc plus souple
                wizardinfo = self.wizard.getwizardinformationsview()
                result['wizardinformations'] = wizardinfo['body']
                reqts['js'].extend(list(wizardinfo['js_links']))
                reqts['css'].extend(list(wizardinfo['css_links']))
                body = item['body']
                body = wizardinfo['body']+body
                item['body'] = body

            result['coordinates'] = {self.coordinates:[item]}
            result['js_links'] = list(reqts['js'])
            result['css_links'] = list(reqts['css'])
        else:
            result = item

        return result

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

    def _chmod(self, form, mask=[]):
        for m in mask:
            node = self._get(form, m[0])
            if node is not None:
                if isinstance(m[1], basestring):
                   if m[1] == u'r':
                       node.widget.readonly = True
                else:
                    self._chmod(node.children[0], m[1])

