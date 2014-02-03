import itertools
import inspect
import sys
import deform
import deform.form
import deform.exception
from substanced.form import FormError


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


class MultipleFormView(object):

    views = ()
    multipleformid = ''
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.viewsinstances = [f(self.context,self.request) for f in self.views]

    def __call__(self):
        counter = itertools.count()
        allforms = {}
        allreqts={'js': [], 'css': []}

        for f in self.viewsinstances:
            form, reqts = f._build_form()
            allreqts['js'].extend(reqts['js'])
            allreqts['css'].extend(reqts['css'])
            allforms[form.formid]= (f, form)
            form.counter = counter

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
                        html.append(e.render())
                    else:
                        try:
                            html = success_method(validated)
                        except FormError as e:
                            snippet = '<div class="error">Failed: %s</div>' % e
                            formview.request.sdiapi.flash(snippet, 'danger',
                                                      allow_duplicate=True)
                            html.append(form.render(validated))
                    break

        if not html:
            tabnav = []
            tabcontent = []
            tabnav.append('<ul  id="' + self.multipleformid + '_multipleform" class="nav nav-pills">')
            tabcontent.append('<div  id="' + self.multipleformid + '_multipleformContent" class="tab-content">')
            isfirst = True
            for formid in allforms:
                statuscontent = 'tab-pane fade'
                statusnav = ''
                if isfirst:
                    statuscontent = 'tab-pane fade in active'
                    statusnav = 'active'
                    isfirst = False
                form = allforms[formid][1]
                view = allforms[formid][0]
                tabnav.append('<li class="' + statusnav + '"><a data-toggle="tab" href="#' + formid + '">' + view.title + '</a></li>')
                tabcontent.append('<div id="' + formid + '" class="' + statuscontent + '">' + form.render() + '</div>')

            tabnav.append('</ul>')
            tabcontent.append('</div>')
            html.extend(tabnav)
            html.extend(tabcontent)

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
