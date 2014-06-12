# -*- coding: utf-8 -*-
from pyramid.httpexceptions import HTTPFound
from zope.interface import implementer
import deform.exception
import deform.widget

from substanced.form import FormView as SubstanceDFormView
from substanced.form import FormError

from pontus.interfaces import IFormView
from pontus.view import ElementaryView, merge_dicts

try:
      basestring
except NameError:
      basestring = str


@implementer(IFormView)
class FormView(ElementaryView, SubstanceDFormView):

    title = 'Form View'
    chmod = []

    def __init__(self, context, request, parent=None, wizard=None, stepid=None, **kwargs):
        self.schema = self.schema.clone()
        SubstanceDFormView.__init__(self, context, request)
        ElementaryView.__init__(self, context, request, parent, wizard, stepid, **kwargs)
        self.buttons = [behavior.title for behavior in self.behaviorinstances.values()]

    def setviewid(self, viewid):
        ElementaryView.setviewid(self, viewid)
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
        self.init_stepid(self.schema)  # TODO: in before_update?
        form, reqts = self._build_form()
        form.formid = self.viewid + '_' + form.formid
        for c in form.children:
            c.oid = c.oid + form.formid

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
                        if button.name != "Cancel":
                            controls = self.request.POST.items()
                            validated = form.validate(controls)
                        else:
                            # bypass form validation for Cancel button
                            validated = {}
                    except deform.exception.ValidationFailure as e:
                        fail = getattr(self, '%s_failure' % button.name, None)
                        if fail is None:
                            fail = self._failure
                        item = fail(e, form)
                        error = True
                    else:
                        try:
                            behavior = self.behaviorinstances[button.name]
                            item = behavior.execute(self.context,
                                    self.request, validated)
                            self.finished_successfully = True
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
            else:
                item = HTTPFound(self.request.resource_url(self.context))

        if isinstance(item, dict):
            if error:
                item['isactive'] = True

            result['coordinates'] = {self.coordinates: [item]}
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

    def _chmod(self, form, mask):
        for m in mask:
            node = self._get(form, m[0])
            if node is not None:
                if isinstance(m[1], basestring):
                   if m[1] == 'r':
                       node.widget.readonly = True
                else:
                    self._chmod(node.children[0], m[1])
