# -*- coding: utf-8 -*-
import itertools
import inspect
import sys
import deform
import deform.form
import deform.exception
from deform.field import Field

from substanced.form import FormError

from pontus.wizard import Step
from pontus.form import FormView


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

PY3 = sys.version_info[0] == 3

if PY3:
    def unicode(val, encoding='utf-8'):
        return val
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer


def get_code(level):
    frame = sys._getframe(level)
    lines, start = inspect.getsourcelines(frame.f_code)
    end = start + len(lines)
    code = ''.join(lines)
    if not PY3:
        code = unicode(code, 'utf-8')
    formatter = HtmlFormatter()
    return highlight(code, PythonLexer(), formatter), start, end


class MultipleFormView(Step):

    views = ()
    multipleformid = ''

    def __init__(self, context, request, wizard = None, index = 0):
        super(MultipleFormView, self).__init__(wizard, index)
        self.context = context
        self.request = request
        self.viewsinstances = [f(self.context, self.request, wizard, index) for f in self.views]

    def _build_form(self):
        allforms = {}
        allMultiforms = {}
        allreqts={'js': [], 'css': []}
        counter = itertools.count()
        for f in self.viewsinstances:
            if f.condition():
                if isinstance(f, FormView):
                    f._setSchemaStepIndexNode()
                    form, reqts = f._build_form()
                    allreqts['js'].extend(reqts['js'])
                    allreqts['css'].extend(reqts['css'])
                    form.formid = self.multipleformid+'_'+form.formid
                    f.formid = form.formid
                    allforms[form.formid]= (f, form)
                    form.counter = counter

                else:
                    forms, multiforms, reqts = f._build_form()
                    allreqts['js'].extend(reqts['js'])
                    allreqts['css'].extend(reqts['css'])
                    f.multipleformid = self.multipleformid+'_'+f.multipleformid
                    allMultiforms[f.multipleformid]= f
                    for submf in multiforms:
                        multiforms[submf].multipleformid = self.multipleformid+'_'+multiforms[submf].multipleformid
                        allMultiforms[multiforms[submf].multipleformid]= multiforms[submf]

                    for subf in forms:
                        forms[subf][1].formid = self.multipleformid+'_'+forms[subf][1].formid
                        forms[subf][0].formid = forms[subf][1].formid
                        allforms[forms[subf][1].formid]= (forms[subf][0], forms[subf][1])

        return allforms, allMultiforms, allreqts

    def _isin(self, itemid, simpel):
        if itemid.startswith(self.multipleformid) and (simpel or ((len(itemid.split('_'))-1) == len(self.multipleformid.split('_')))):
            return True

        return False

    def _getAllsubforms(self, allforms):
        result = {}
        for formid in allforms:
            if self._isin(formid, False):
                result[formid]=(allforms[formid][0],allforms[formid][1])

        return result

    def _getAllsubmultiforms(self, allmultiforms):
        result = {}
        for formid in allmultiforms:
            if self._isin(formid, False):
                result[formid]=allmultiforms[formid]

        return result
 
    def _html(self, allforms, allmultiforms, currentform = None, exception = None ,validated = None):
        html = []
        tabnav = []
        tabcontent = []
        allsubforms = self._getAllsubforms(allforms)
        allsubmultiforms = self._getAllsubmultiforms(allmultiforms)
        tabnav.append('<ul  id="' + self.multipleformid + '_multipleform" class="nav nav-tabs ">')
        tabcontent.append('<div  id="' + self.multipleformid + '_multipleformContent" class="tab-content">')
        nocurrentform = False
        currentmultform = None
        if currentform is None:
            nocurrentform = True
            for item in self.viewsinstances:
                if isinstance(item, FormView) and item.formid in allsubforms:
                    currentform = item.formid
                    break
               
                if isinstance(item, MultipleFormView) and item.multipleformid in allsubmultiforms:
                    currentmultform = item.multipleformid
                    break                    

        for item in self.viewsinstances:
            if isinstance(item, FormView) and item.formid in allsubforms:
                formid = item.formid
                form = allsubforms[formid][1]
                view = allsubforms[formid][0]
                if currentform == formid:
                    renderer = ''
                    if validated is not None:
                        renderer = form.render(validated)
                    elif exception is not None:
                        renderer = exception.render()
                    else:
                        renderer = form.render()

                    tabcontent.append('<div id="' + formid + '" class="tab-pane fade in active">' + renderer + '</div>')
                    tabnav.append('<li class="active"><a data-toggle="tab" href="#' + formid + '">' + view.title + '</a></li>')
                else:
                    tabcontent.append('<div id="' + formid + '" class="tab-pane fade">' + form.render() + '</div>')
                    tabnav.append('<li class=""><a data-toggle="tab" href="#' + formid + '">' + view.title + '</a></li>')

            elif isinstance(item, MultipleFormView) and item.multipleformid in allsubmultiforms: 
                formid = item.multipleformid
                view = allsubmultiforms[formid]
                if not nocurrentform and currentform is not None and view._isin(currentform, True):
                    tabcontent.append('<div id="' + formid + '" class="tab-pane fade in active">' + ''.join(view._html(allforms, allmultiforms, currentform, exception ,validated)) + '</div>')
                    tabnav.append('<li class="active"><a data-toggle="tab" href="#' + formid + '">' + view.title + '</a></li>')
                elif nocurrentform and currentmultform is not None and currentmultform == formid :
                    tabcontent.append('<div id="' + formid + '" class="tab-pane fade in active">' + ''.join(view._html(allforms, allmultiforms, None, exception ,validated)) + '</div>')
                    tabnav.append('<li class="active"><a data-toggle="tab" href="#' + formid + '">' + view.title + '</a></li>')
                else:
                    tabcontent.append('<div id="' + formid + '" class="tab-pane fade">' + ''.join(view._html(allforms, allmultiforms, None, exception ,validated)) + '</div>')
                    tabnav.append('<li class=""><a data-toggle="tab" href="#' + formid + '">' + view.title + '</a></li>')

        tabnav.append('</ul>')
        tabcontent.append('</div>')
        html.extend(tabnav)
        html.extend(tabcontent)
        return html

    def __call__(self):
        allforms, allmultiforms, allreqts = self._build_form()
        html = []
        validated = None
        posted_formid = None
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
                        html = self._html(allforms, allmultiforms, posted_formid, e, validated)
                    else:
                        try:
                            html = success_method(validated)
                            self.esucces = True
                        except FormError as e:
                            snippet = '<div class="error">Failed: %s</div>' % e
                            formview.request.sdiapi.flash(snippet, 'danger',
                                                      allow_duplicate=True)
                            html = self._html(allforms, allmultiforms, posted_formid, None, validated)

                    break
        
        if not html:
            html = self._html(allforms, allmultiforms, posted_formid, None, validated)

        code, start, end = get_code(1)
        if isinstance(html, list):
            html = ''.join(html)
            result = {
                'form': html,
                'captured': repr(validated),
                'code': code,
                'start': start,
                'showmenu': True,
                'end': end,
                'title': self.title,
                'js_links': list(set(allreqts['js'])),
                'css_links': list(set(allreqts['css'])),
                }
        else:
            result = html

        # values passed to template for rendering
        return result
