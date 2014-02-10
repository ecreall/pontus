# -*- coding: utf-8 -*-
from substanced.form import FormView


class FormView(FormView):

    chmod = []

    # Il faut partir de l'idée que toute est étape et non l'inverse.
    # Une étape a une condition permettant de la validé. True par défaut
    def condition(self):
        return True

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

    def before(self, form):
        self._chmod(form, self.chmod)
