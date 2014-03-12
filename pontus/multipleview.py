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


def default_builder(mview, views):
    if views is None:
        return

    for view in views:
        if isinstance(view, tuple):
            mf = MultipleView(mview.context, mview.request, mview, mview.wizard, mview.index)
            mf.title = view[0]
            mf.viewid = mview.viewid+'_'+mf.title.replace(' ','-')
            mf.builder(view[1])
            mview.children.append(mf)
        else:
            mview.children.append(view(mview.context, mview.request, mview, mview.wizard, mview.index))        


class MultipleView(View):

    views = ()
    builder = default_builder
    item_template = 'templates/submultipleview.pt'

    def __init__(self, context, request, parent=None, wizard=None, index=0):
        super(MultipleView, self).__init__(context, request, parent, wizard, index)
        self.children = []
        self._slots = []
        self.builder(self.views)

    def _merg(self, source, target):
        result = target
        for k in source.keys():
            if k in result.keys():
                if isinstance(result[k], list):
                    result[k].extend(source[k])
                elif isinstance(result[k], dict):
                    result[k] = self._merg(source[k], result[k])
            else:
                result[k] = source[k]
       
        return result

    def _activate(self, items):
        if items:
            item = items[0]
            item['isactive'] = True
            if 'items' in item:
                self._activate(item['items'])

    def update(self,):
        result = {}
        for view in self.children:
            view_result = view.update()
            if not isinstance(view_result,dict):
                return view_result
       
            result = self._merg(view_result, result)

        for slot in result['slots']:
            items = result['slots'][slot]
            isactive = False
            for item in items:
                if item['isactive']:
                    isactive = True
            
            if not isactive:
                self._activate(items)
                if self.parent is None:
                    isactive = True

            result['slots'][slot] = [{'isactive':isactive,
                                      'items': items,
                                      'view': self,
                                      'id':self.viewid}]

        return result

