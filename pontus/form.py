# -*- coding: utf-8 -*-
from zope.interface import implements
import deform.exception
import deform.widget
import colander

from substanced.schema import Schema
from substanced.form import FormView as FV, FormError

from pontus.wizard import Step, STEPID
from pontus.visual import VisualisableElement
from pontus.interfaces import IFormView
# Il faut partir de l'idée que toute est étape et non l'inverse.
# Une étape a une condition permettant de la validé. True par défaut



class FormView(VisualisableElement, Step, FV):
    implements(IFormView)

    chmod = []

    def __init__(self, context, request, wizard = None, index = 0, **kwargs):
        FV.__init__(self, context, request)
        Step.__init__(self, wizard, index)
        VisualisableElement.__init__(self, **kwargs)
        
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

    def __call__(self):
        self._setSchemaStepIndexNode()
        form, reqts = self._build_form()
        result = None
        for button in form.buttons:
            if button.name in self.request.POST:
                success_method = getattr(self, '%s_success' % button.name)
                try:
                    controls = self.request.POST.items()
                    validated = form.validate(controls)
                except deform.exception.ValidationFailure as e:
                    fail = getattr(self, '%s_failure' % button.name, None)
                    if fail is None:
                        fail = self.failure
                    result = fail(e)
                else:
                    try:
                        result = success_method(validated)
                        self.esucces = True
                    except FormError as e:
                        snippet = '<div class="error">Failed: %s</div>' % e
                        self.request.sdiapi.flash(snippet, 'danger',
                                                  allow_duplicate=True)
                        result = {'form': form.render(validated)}

                break

        if result is None:
            result = self.show(form)

        if isinstance(result, dict):
            result['js_links'] = reqts['js']
            result['css_links'] = reqts['css']

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
        

