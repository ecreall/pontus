# -*- coding: utf-8 -*-
import itertools
import inspect
import sys
import deform
import deform.form
import deform.exception
from deform.field import Field
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from pyramid_layout.layout import Structure
from pyramid.renderers import get_renderer
from pyramid import renderers

from substanced.form import FormError

from pontus.wizard import Step
from pontus.form import FormView
from pontus.view import View
from pontus.util import get_view


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

PY3 = sys.version_info[0] == 3

if PY3:
    def unicode(val, encoding='utf-8'):
        return val


def get_code(level):
    frame = sys._getframe(level)
    lines, start = inspect.getsourcelines(frame.f_code)
    end = start + len(lines)
    code = ''.join(lines)
    if not PY3:
        code = unicode(code, 'utf-8')
    formatter = HtmlFormatter()
    return highlight(code, PythonLexer(), formatter), start, end
               

class MultipleView(View):

    views = ()

    def __init__(self, context, request, parent=None, wizard=None, index=0):
        super(MultipleView, self).__init__(context, request, wizard, index)
        self.children = []
        self._slots = []
        if self.views:      
            self._buildMultiViewTree(self.views)

    def _buildMultiViewTree(self, views):
        for view in views:
            if isinstance(view, tuple):
                mf = MultipleView(self.context, self.request, self, self.wizard, self.index)
                mf.title = view[0]
                mf.viewid = mf.title.replace(' ','-')
                mf._buildMultiViewTree(view[1])
                self.children.append(mf)
            else:
                self.children.append(view(self.context, self.request, self, self.wizard, self.index))

    def _build_view(self):
        allforms = {}
        allMultiviews = {}
        allviews = {}
        allreqts = {'js': [], 'css': []}
        counter = itertools.count()
        for f in self.children:
            if f.condition():
                if isinstance(f, FormView):
                    f._setSchemaStepIndexNode()
                    form, reqts = f._build_form()
                    allreqts['js'].extend(reqts['js'])
                    allreqts['css'].extend(reqts['css'])
                    form.formid = self.viewid+'_'+form.formid
                    f.setviewid(form.formid)
                    allforms[form.formid]= (f, form)
                    form.counter = counter
                    self._slots.append(f.slot)
                elif isinstance(f, MultipleView):
                    forms, multiviews, allsubviews, reqts = f._build_view()
                    allreqts['js'].extend(reqts['js'])
                    allreqts['css'].extend(reqts['css'])
                    f.setviewid(self.viewid+'_'+f.viewid)
                    allMultiviews[f.viewid]= f
                    self._slots.extend(f._slots)
                    for submf in multiviews:
                        multiviews[submf].setviewid(self.viewid+'_'+multiviews[submf].viewid)
                        allMultiviews[multiviews[submf].viewid]= multiviews[submf]

                    for subf in forms:
                        forms[subf][1].formid = self.viewid+'_'+forms[subf][1].formid
                        forms[subf][0].setviewid(forms[subf][1].formid)
                        allforms[forms[subf][1].formid]= (forms[subf][0], forms[subf][1])

                    for subv in allsubviews:
                        allsubviews[subv].setviewid(self.viewid+'_'+allsubviews[subv].viewid)
                        allviews[allsubviews[subv].viewid]= allsubviews[subv]

                elif isinstance(f, View):
                    f.context = self.context.propositions[0] # pour le test
                    result = f()
                    self._slots.append(f.slot)
                    if isinstance(result, dict):
                        allreqts['js'].extend(result['js_links'])
                        allreqts['css'].extend(result['css_links'])

                    f.setviewid(self.viewid+'_'+f.viewid)
                    allviews[f.viewid]= f

        return allforms, allMultiviews, allviews, allreqts

    def _isin(self, itemid, simpel):
        if itemid.startswith(self.viewid) and not (itemid == self.viewid) and (simpel or ((len(itemid.split('_'))-1) == len(self.viewid.split('_')))):
            return True

        return False

    def _getAllsubforms(self, slot, allforms):
        result = {}
        for formid in allforms:
            formview = allforms[formid][0]
            if self._isin(formid, False) and formview.slot == slot:
                result[formid]=(formview,allforms[formid][1])

        return result

    def _getAllsubmultiviews(self, slot, allMultiviews):
        result = {}
        for viewid in allMultiviews:
            view = allMultiviews[viewid]
            if self._isin(viewid, False) and slot in view._slots:
                result[viewid]=view

        return result

    def _getAllsubviews(self, slot, allviews):
        result = {}
        for viewid in allviews:
            view = allviews[viewid]
            if self._isin(viewid, False) and view.slot == slot:
                result[viewid]=view

        return result

    def _allslots(self, allforms, allMultiviews, allviews, currentitem=None, exception=None ,validated=None):
        slots = {}
        for slot in self._slots:
            slots[slot] = self._itemsbyslot(slot ,allforms, allMultiviews, allviews, currentitem, exception ,validated)
     
        return slots
     
    def _itemsbyslot(self, slot ,allforms, allMultiviews, allviews, currentitem=None, exception=None ,validated=None):
        itemsbyslot = []
        allitems = []
        allsubforms = self._getAllsubforms(slot, allforms)
        allsubmultiviews = self._getAllsubmultiviews(slot, allMultiviews)
        allsubviews = self._getAllsubviews(slot, allviews)
        allitems.extend(allsubforms.keys())
        allitems.extend(allsubmultiviews.keys())
        allitems.extend(allsubviews.keys())
        if currentitem is None:
            for item in self.children:
                if item.viewid in allitems:
                    currentitem = item.viewid
                    break

        for item in self.children:
            itemid = None
            view = None
            body = None
            isactive = False
            if isinstance(item, FormView) and item.formid in allsubforms:
                itemid = item.formid
                form = allsubforms[itemid][1]
                view = allsubforms[itemid][0]
                if currentitem == itemid:
                    if validated is not None:
                        body = form.render(validated)
                    elif exception is not None:
                        body = exception.render()
                    else:
                        body = form.render()

                    isactive = True
                else:
                    body = form.render()

                itemsbyslot.append({'isactive':isactive,'body': body, 'view': view, 'id':itemid})
            elif isinstance(item, MultipleView) and item.viewid in allsubmultiviews: 
                itemid = item.viewid
                view = allsubmultiviews[itemid]
                items = []
                if (currentitem is not None and view._isin(currentitem, True)):
                    items = view._itemsbyslot(slot, allforms, allMultiviews, allviews, currentitem, exception ,validated)
                    isactive = True
                elif (currentitem is not None and currentitem == itemid):
                    items = view._itemsbyslot(slot, allforms, allMultiviews, allviews, None, None ,None)
                    isactive = True
                else:
                    items = view._itemsbyslot(slot, allforms, allMultiviews, allviews, None, None ,None)

                itemsbyslot.append({'isactive':isactive,'items': items, 'view': view, 'id':itemid})
            elif isinstance(item, View) and item.viewid in allsubviews:
                itemid = item.viewid
                view = allsubviews[itemid]
                result = view.update()
                subitem = result['slots'][slot][0]
                body = subitem['body']
                if (currentitem is not None and currentitem == itemid):
                    isactive = True
                
                subitem_result= {'isactive':isactive,'body': body, 'view': view, 'id':itemid}
                if 'messages' in subitem:
                    subitem_result['messages'] = subitem['messages']

                itemsbyslot.append(subitem_result)

        return itemsbyslot

    def update(self,):
        allforms, allMultiviews, allviews, allreqts = self._build_view()
        slots = []
        validated = None
        posted_formid = None
        result = None
        if '__formid__' in self.request.POST:
            posted_formid = self.request.POST['__formid__']

        if posted_formid is not None and posted_formid in allforms:
            formview = allforms[posted_formid][0]
            form = allforms[posted_formid][1]
            for button in form.buttons:
                if button.name in self.request.POST:
                    success_method = getattr(formview, '%s_success' % button.name)
                    try:
                        controls = self.request.POST.items()
                        validated = form.validate(controls)
                    except deform.exception.ValidationFailure as e:
                        fail = getattr(formview, '%s_failure' % button.name, None)
                        if fail is None:
                            fail = formview.failure
                        slots = self._allslots(allforms, allMultiviews, allviews, posted_formid, e, validated)
                    else:
                        try:
                            slots = success_method(validated)
                            self.esucces = True
                        except FormError as e:
                            snippet = '<div class="error">Failed: %s</div>' % e
                            formview.request.sdiapi.flash(snippet, 'danger',
                                                      allow_duplicate=True)
                            slots = self._allslots(allforms, allMultiviews, allviews, posted_formid, None, validated)

                    break

        if not slots:
            slots = self._allslots(allforms, allMultiviews, allviews, posted_formid, None, validated)

        code, start, end = get_code(1)
        if isinstance(slots, dict):
            result = {
                'slots': slots,
                'captured': repr(validated),
                'code': code,
                'start': start,
                'showmenu': True,
                'end': end,
                'title': self.title,
                'js_links': list(set(allreqts['js'])),
                'css_links': list(set(allreqts['css']))
                }
        else:
            result = slots

        # values passed to template for rendering
        return result
