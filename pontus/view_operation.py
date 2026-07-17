# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi

"""The composition algebra of views.

Operations share the ``views``/``contexts`` class attributes (values
or callables) and compose through the result contract by deep merge:
``MultipleView`` (several views, one context — the tabs),
``CallView`` (one view class, several contexts — the accordion),
``MergedFormsView`` (one form over several contexts, buttons suffixed
*All*, per-context dispatch), ``CallSelectedContextsViews`` (checkbox
selection + one button per operation, routed to the two above), and
``Wizard`` (a step graph of views mirroring the dace behaviour-level
wizard, current step in the session).
"""
import re
import deform.widget
import colander
import itertools
from pyramid.httpexceptions import HTTPFound

from substanced.form import FormError
from substanced.util import get_oid

from dace.util import get_obj
from pontus.schema import Schema
from pontus.view import View, ViewError
from pontus.util import merge_dicts
from pontus.form import FormView
from pontus.widget import (
        SimpleFormWidget,
        AccordionWidget,
        SimpleMappingWidget,
        CheckboxChoiceWidget)
from pontus.interfaces import IFormView
from pontus.resources import (
        CallViewErrorPrincipalmessage,
        CallViewViewErrorCauses,
        MutltipleViewErrorPrincipalmessage,
        MutltipleViewErrorCauses,
        CallViewErrorCildrenNotValidatedmessage)
from pontus.core import STEPID, Step


def default_view(callview):
    """Default ``view`` callable: none."""
    return None


def default_views(callview):
    """Default ``views`` callable: empty."""
    return []


def default_contexts(callview):
    """Default ``contexts`` callable: empty."""
    return []


def default_context(callview):
    """Default single-context callable: the operation context."""
    return callview.context


class ViewOperation(View):

    """Base operation: resolves ``views``/``contexts``, tracks validated/failed children."""
    merged = False
    contexts = default_contexts
    views = default_views

    def __init__(self, 
                 context, 
                 request, 
                 parent=None, 
                 wizard=None, 
                 stepid=None, 
                 **kwargs):
        super(ViewOperation, self).__init__(context, request, parent, 
                                            wizard, stepid, **kwargs)
        self.errors = []
        if hasattr(self.views, '__func__'):
            self.views = self.views.__func__

        if type(self.views).__name__ == 'function':
            self.views = self.views(self)

        if not isinstance(self.views,(list, tuple, dict)):
            self.views = [self.views]

        self.contexts = self.contexts()
        self.validated_children = []
        self.failed_children = []

    @property
    def all_children(self):
        """Validated then failed children."""
        result = list(self.validated_children)
        result.extend(list(self.failed_children))
        return result

    def _request_configuration(self):
        """Also honour the ``tomerge`` request param."""
        super(ViewOperation, self)._request_configuration()
        tomerge = self.params('tomerge')
        if tomerge is not None:
            self.merged = bool(tomerge)

    def define_executable(self):
        """Return if the operation is executable or not"""
        return self.isexecutable


class MultipleViewsOperation(ViewOperation):
    """Marker: several views over one context."""
    pass


class MultipleContextsOperation(ViewOperation):

    """One view class instantiated per context (validation splits the children)."""
    def __init__(self, 
                 context, 
                 request, 
                 parent=None, 
                 wizard=None, 
                 stepid=None, 
                 **kwargs):
        super(MultipleContextsOperation, self).__init__(context, request, 
                                           parent, wizard, stepid, **kwargs)
        self.view = None
        if self.views:
            self.view = self.views[0]

        if self.view is not None:
            self._init_children(self.contexts)


    def _init_children(self, contexts=None):
        """Instantiate the view on each context; sort validated/failed."""
        if contexts is None:
            contexts = self.contexts

        self.validated_children = []
        if not isinstance(contexts, (list, tuple)):
            contexts = [contexts]

        for item_context in contexts:
            subview = self.view(item_context, self.request, self,
                                self.wizard, self.stepid,**{})
            try:
                subview.validate()
                self.validated_children.append(subview)
            except ViewError as error:
                self.failed_children.append(subview)
                self.errors.append((subview, error))

    def has_id(self, id):
        """Does any validated child match ``id``?"""
        for view in self.validated_children:
            if view.has_id(id):
                return True

        return False

    def get_view_requirements(self):
        """Children's requirements merged with the operation's."""
        result = self.requirements_copy
        for view in self.validated_children:
            view_requirements = view.get_view_requirements()
            result = merge_dicts(view_requirements, result)

        return result


class MultipleContextsViewsOperation(ViewOperation):
    """Marker: several views over several contexts."""
    pass


def default_builder(parent, views, **kwargs):
    """Default ``MultipleView`` builder: views and nested ``(title,
    [views])`` tuples become validated children (or sub-multiple-views),
    inheriting the coordinates when merged.
    """
    if views is None:
        return

    for view in views:
        if isinstance(view, tuple):
            viewinstance = MultipleView(parent.context, parent.request, 
                          parent, parent.wizard, parent.stepid, **kwargs)
            viewinstance.merged = parent.merged
            if parent.merged:
                viewinstance.coordinates = parent.coordinates

            viewinstance.title = view[0]
            viewinstance.builder(view[1])
            if viewinstance.validated_children:
                parent.validated_children.append(viewinstance)
            else:
                parent.failed_children.append(viewinstance)

        else:
            viewinstance = view(parent.context, parent.request, 
                 parent, parent.wizard, parent.stepid, **kwargs)
            try:
                viewinstance.validate()
                parent.validated_children.append(viewinstance)
            except ViewError as error:
                parent.errors.append((viewinstance, error))
                parent.failed_children.append(viewinstance)
                
            if parent.merged:
                viewinstance.coordinates = parent.coordinates


class MultipleView(MultipleViewsOperation):

    """Several views on one context, composed as tabs (see module docstring)."""
    title = 'Multiple View'
    name = 'multipleview'
    builder = default_builder
    include_failed_views = False
    template = 'templates/views_templates/multipleview.pt'

    def __init__(self,
                 context,
                 request,
                 parent=None,
                 wizard=None,
                 stepid=None,
                 **kwargs):
        super(MultipleView, self).__init__(context, request, parent,
                                            wizard, stepid, **kwargs)
        self._coordinates = []
        if self.views:
            self._init_views(self.views, **kwargs)

    def _init_views(self, views, **kwargs):
        """Build the children through ``builder`` and recompute executability."""
        self.validated_children = []
        self.builder(views, **kwargs)
        self.define_executable()

    def get_view_requirements(self):
        """Children's requirements merged with the operation's."""
        result = self.requirements_copy
        for view in self.validated_children:
            view_requirements = view.get_view_requirements()
            result = merge_dicts(view_requirements, result)

        return result

    def define_executable(self):
        """Executable iff any child is; born finished otherwise."""
        self.isexecutable = False
        self.finished_successfully = True
        for child in self.validated_children:
            if child.isexecutable:
                self.isexecutable = True
                self.finished_successfully = False
                break

        return self.isexecutable

    def _activate(self, items):
        """Force the first item (recursively) active."""
        if items:
            item = items[0]
            item['isactive'] = True
            if 'items' in item:
                self._activate(item['items'])

    def before_update(self):
        """Bind, then prepare every validated child."""
        self.bind()
        for view in self.validated_children:
            view.before_update()


    def has_id(self, id):
        """Does any validated child match ``id``?"""
        for view in self.validated_children:
            if view.has_id(id):
                return True

        return False

    def _update_all_children(self):
        """Update children including failures (rendered via ``failure``)."""
        result = {}
        for view in self.all_children:
            try:
                if view in self.failed_children:
                    error = dict(self.errors)[view]
                    view_result = view.failure(error)
                else:
                    view_result = view.update()
            except ViewError as e:
                continue

            if self.isexecutable and view.isexecutable and \
               view.finished_successfully:
                self.finished_successfully = True
                #for wizards
                view.init_stepid()
                return self.success(view_result)

            if not isinstance(view_result, dict):
                return view_result

            result = merge_dicts(view_result, result)

        return result

    def _update_validated_children(self):
        """Update the validated children, short-circuiting on success."""
        result = {}
        for view in self.validated_children:
            try:
                view_result = view.update()
            except ViewError as e:
                continue

            if self.isexecutable and view.isexecutable and \
               view.finished_successfully:
                self.finished_successfully = True
                #for wizards
                view.init_stepid()
                return self.success(view_result)

            if not isinstance(view_result, dict):
                return view_result

            result = merge_dicts(view_result, result)

        return result

    def update(self,):
        #validation
        """Merge the children results, keep one active item per slot, and wrap
        each slot in the multiple-view template — or raise ``ViewError`` when
        nothing rendered.
        """
        if not self.validated_children and \
           not self.include_failed_views:
            error = ViewError()
            error.principalmessage = MutltipleViewErrorPrincipalmessage
            causes = set()
            for viewinstance, er in self.errors:
                causes.update(er.causes)

            error.causes = list(causes)
            raise error

        #update children
        result = {}
        if self.include_failed_views:
            result = self._update_all_children()
        else:
            result = self._update_validated_children()

        if not result:
            error = ViewError()
            error.principalmessage = MutltipleViewErrorPrincipalmessage
            error.causes = MutltipleViewErrorCauses
            raise error

        if not isinstance(result, dict):
            return result

        for _coordinate in result['coordinates']:
            coordinate = _coordinate
            if self.merged:
                coordinate = self.coordinates

            items = result['coordinates'][coordinate]
            isactive = False
            for item in items:
                if item['isactive']:
                    isactive = True
                    break

            if not isactive:
                self._activate(items)
                if self.parent is None:
                    isactive = True

            _item = {'isactive':isactive,
                      'items': items,
                      'view': self,
                      'id':self.viewid}
            values = {'coordinates': coordinate, 
                      'subitem': _item, 
                      'parent': self}
            body = self.content(args=values, template=self.template)['body']
            item = self.adapt_item(body, self.viewid)
            item['isactive'] = isactive
            result['coordinates'][coordinate] = [item]
            result = merge_dicts(self.requirements_copy, result)

        return result


    def adapt_item(self, render, id, isactive=True):
        """Mark the item as a multiple view."""
        item  = super(MultipleView, self).adapt_item(render, id, isactive)
        item['ismultipleview'] = True
        return item

    def after_update(self):
        """Close the (successful) children."""
        if self.finished_successfully:
            for view in self.validated_children:
                view.after_update()
        else:
            for view in self.validated_children:
                if view.finished_successfully:
                    view.after_update()

    def success(self, validated=None):
        """Pass the successful child result through (redirect)."""
        return validated


class ViewSchema(Schema):

    """Hidden per-subform identity (id, context oid, title) of merged forms."""
    id = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.HiddenWidget()
                )

    context_oid = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.HiddenWidget()
                )

    title = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.HiddenWidget()
                )


class EmptySchema(Schema):
    """The ``views`` sequence holding one entry per context in merged forms."""
    views = colander.SchemaNode(
                colander.Sequence(),
                ViewSchema(name='view', widget=SimpleMappingWidget())
            )


class MergedFormsView(MultipleContextsOperation, FormView):
    """One form over several contexts: the subview's schema is embedded as
    the ``item`` of each ``views`` entry, buttons are suffixed, and each
    validated entry is dispatched to the behaviour of the matching
    subform (by ``context_oid`` and viewid).
    """
    title = 'MergedFormsView'
    name = 'mergedformsview'
    schema = EmptySchema(widget=SimpleFormWidget())
    widget = AccordionWidget()
    suffixe = 'All'

    def __init__(self, 
                 context, 
                 request, 
                 parent=None, 
                 wizard=None, 
                 stepid=None, 
                 **kwargs):
        self.schema = self.schema.clone()
        super(MergedFormsView, self).__init__(context, request, parent,
                                               wizard, stepid, **kwargs)
        self.buttons = [b.title+' '+self.suffixe for b in self.view.behaviors]
        self._addItemsNode()

    def _init_children(self, contexts):
        """Instantiate the subforms and index them by context oid."""
        MultipleContextsOperation._init_children(self, contexts)
        items = self.validated_children
        self.children_by_context = {}
        for subform in items:
            context_oid = str(get_oid(subform.context))
            if context_oid in self.children_by_context:
                self.children_by_context[context_oid].append(subform)
            else:
                self.children_by_context[context_oid] = [subform]

    def _addItemsNode(self):
        """Embed the subview's schema as the ``item`` of the views sequence."""
        if self.schema.get('views').children[0].get('item') is not None:
            self.schema.get('views').children[0].__delitem__('item') #return

        schema = self.view.schema.clone()
        schema.name = 'item'
        schema.widget = SimpleMappingWidget()
        viewsschemanode = self.schema.get('views')
        viewsschemanode.widget = self.widget
        viewsschemanode.children[0].children.append(schema)


    def before_update(self):
        """Prepare every child (failed ones included: their errors are shown)."""
        self.bind()
        for view in self.all_children:
            view.before_update()

    def update(self,):
        """Build the merged form; on submit, validate then run the matching
        subform behaviour per entry; render warnings for the children that
        did not validate.
        """
        if not self.children_by_context:
            error = ViewError()
            error.principalmessage = CallViewErrorPrincipalmessage
            causes = set()
            for view, er in self.errors:
                causes.update(er.causes)

            error.causes = list(causes)
            raise error

        messages = {}
        if self.failed_children:
            error = ViewError()
            error.type = 'warning'
            error.principalmessage = CallViewErrorCildrenNotValidatedmessage
            error.causes = CallViewViewErrorCauses
            messages[error] = error.render_message(self.request)

        self.init_stepid(self.schema)
        form, reqts = self._build_form()
        form.formid = self.viewid+'_'+form.formid
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
                        #@TODO gestion des _failure des vues
                        fail = getattr(self, '%s_failure' % button.name, None)
                        if fail is None:
                            fail = self._failure
                        item = fail(e, form)
                        error = True
                    else:
                        try:
                            views = validated['views']
                            for v in views:
                                views_context = None
                                if v['context_oid'] in self.children_by_context:
                                    views_context = self.children_by_context[v['context_oid']]
                                else:
                                    continue

                                view_instance = None
                                for v_context in views_context:
                                    if v_context.viewid == v['id']:
                                        view_instance = v_context
                                        break

                                if view_instance is None:
                                    continue

                                bname = button.name.replace(('_'+self.suffixe), '')
                                if bname in view_instance.behaviors_instances:
                                    behavior = view_instance.behaviors_instances[bname]
                                    behavior.execute(view_instance.context, 
                                                     self.request, v['item'])
                                    view_instance.finished_successfully = True

                            item = self.success(validated)
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
            item = self.show(form)

        if isinstance(item,dict):
            if error:
                item['isactive'] = True

            if messages:
                item['messages'] = {}
                for e, messagecontent in messages.items():
                    if e.type in item['messages']:
                        item['messages'][e.type].append(messagecontent)
                    else:
                        item['messages'][e.type] = [messagecontent]

            result['coordinates'] = {self.view.coordinates:[item]}
            result['js_links'] = reqts['js']
            result['css_links'] = reqts['css']
            result = merge_dicts(self.requirements_copy, result)

        else:
            result = item

        return result

    def after_update(self):
        """Close every child once the whole operation succeeded."""
        if self.finished_successfully:
            for view in self.all_children:
                view.after_update()

    def success(self, validated):
        """Redirect to the context's ``@@index``."""
        return HTTPFound(
            self.request.resource_url(self.context, '@@index'))

    def default_data(self):
        """One pre-filled entry per subform (id, context oid, title, item)."""
        result = {'views':[]}
        views = list(itertools.chain.from_iterable(
                          list(self.children_by_context.values())))
        for item in views:
            item_default_data = item.default_data()
            if item_default_data is None:
                item_default_data = {}
            item_default_data = {'item': item_default_data,
                                 'id': item.viewid,
                                 'context_oid':str(get_oid(item.context)),
                                 'title':item.context.title}
            result['views'].append(item_default_data)

        return result


class CallView(MultipleContextsOperation):

    """One view class over several contexts, aggregated per slot (accordion)."""
    title = 'CallView'
    name = 'callview'
    template = 'pontus:templates/views_templates/global_accordion.pt'

    def __init__(self, 
                 context, 
                 request, 
                 parent=None, 
                 wizard=None, 
                 stepid=None, 
                 **kwargs):
        super(CallView, self).__init__(context, request, parent,
                                       wizard, stepid, **kwargs)
        self.define_executable()

    def define_executable(self):
        """Executable iff any child is; born finished otherwise."""
        _isexecutable = False
        for child in self.validated_children:
            if child.isexecutable:
                _isexecutable = True
                break

        if not _isexecutable:
            self.isexecutable = False
            self.finished_successfully = True

        return self.isexecutable

    def before_update(self):
        """Bind, then prepare every validated child."""
        self.bind()
        for view in self.validated_children:
            view.before_update()

    def update(self,):
        """Update every validated child, short-circuit on an executable
        success, then wrap the collected items of each slot in the accordion
        template.
        """
        if not self.validated_children:
            e = ViewError()
            e.principalmessage = CallViewErrorPrincipalmessage
            causes = set()
            for view, er in self.errors:
                causes.update(er.causes)

            e.causes = list(causes)
            raise e

        result = {}
        global_result = {}
        for view in self.validated_children:
            try:
                view_result = view.update()
            except ViewError as e:
                continue

            if self.isexecutable and \
               view.isexecutable and \
               view.finished_successfully:
                self.finished_successfully = True
                return self.success(view_result)

            currentview = view
            if 'view' in view_result:
                currentview = view_result['view']

            global_result = merge_dicts(view_result, global_result)
            if len(view_result['coordinates']) == 1 and \
               len(next(iter(view_result['coordinates'].values()))) == 1:
                # Phase 3 / M2: this branch subscripted dict.items(),
                # which crashes on any Python 3 — it was therefore
                # unreachable since the py3 migration. Regression test:
                # test_CallView_single_coordinate.
                coordinate, values = next(
                    iter(view_result['coordinates'].items()))
                item = values[0]
                if coordinate in result:
                    result[coordinate].append(item)
                else:
                    result[coordinate] = [item]
            else:
                for coordinate, values in view_result['coordinates'].items():
                    item = values[0]
                    subviewid = currentview.viewid+'_'+coordinate
                    item['id'] = subviewid
                    if coordinate in result:
                        result[coordinate].append(item)
                    else:
                        result[coordinate] = [item]

        for coordinate, items in result.items():
            values = {'items': items, 'id':self.viewid+coordinate }
            body = self.content(args=values, template=self.template)['body']
            item = self.adapt_item(body, self.viewid)
            global_result['coordinates'][coordinate] = [item]

        #if not (len(self.validated_children) == len(self.contexts)):
        #    global_result['messages']
        global_result = merge_dicts(self.requirements_copy, global_result)
        return  global_result

    def after_update(self):
        """Re-prepare the (successful) children."""
        if self.finished_successfully:
            for view in self.validated_children:
                view.before_update()
        else:
            for view in self.validated_children:
                if view.finished_successfully:
                    view.before_update()

    def success(self, validated=None):
        """Pass the successful child result through."""
        return validated


class ItemsSchema(Schema):
        """The context-selection node of the batch pattern."""
        items = colander.SchemaNode(
            colander.Set()
            )


class CallSelectedContextsViews(FormView, MultipleContextsViewsOperation):

    """The batch pattern: check contexts, pick an operation (one button per
    target view), route to ``MergedFormsView`` (form target) or
    ``CallView``, round-tripping the selection via the ``__viewid__`` /
    ``__contextsoids__`` hidden nodes.
    """
    title = 'CallSelectedContextsViews'
    name = 'callselectedcontextsviews'
    #widgets
    items_widget = CheckboxChoiceWidget
    form_widget = SimpleFormWidget
    schema = ItemsSchema

    def __init__(self, 
                 context, 
                 request, 
                 parent=None, 
                 wizard=None, 
                 stepid=None, 
                 **kwargs):
        self.schema = self.schema(widget=self.form_widget())
        self.schema = self.schema.clone()
        super(CallSelectedContextsViews, self).__init__(context, request, 
                                        parent, wizard, stepid, **kwargs)
        self.validated_items = []
        self.validated_children = {}
        self._additemswidget()
        self._init_children()
        self.buttons = [b.title for b in self.views]

    def _init_children(self):
        """One CallView/MergedFormsView per target view, keyed by title."""
        for view in self.views:
            name = re.sub(r'\s', '_', view.title)
            base_class = CallView
            if IFormView.implementedBy(view):
                base_class = MergedFormsView

            # a per-target subclass: the shared operation classes are
            # no longer mutated
            multiplecontextsview_class = type(
                base_class.__name__, (base_class,),
                {'title': view.title, 'views': view})
            view_instance = multiplecontextsview_class(self.context, 
                                            self.request, self.parent,
                                            self.wizard, self.stepid)
            self.validated_children[name] = view_instance

    def has_id(self, id):
        """Does any child operation match ``id``?"""
        for view in self.validated_children.values():
            if view.has_id(id):
                return True

        return False

    def _additemswidget(self):
        """Checkbox widget over the candidate contexts (rendered snippets)."""
        values = [(i, i.get_view(self.request)) for i in self.contexts]
        widget = self.items_widget(values=values, multiple=True)
        viewsschemanode =  self.schema.get('items')
        viewsschemanode.widget = widget

    def update(self,):
        """Show/validate the selection form, or answer a child form post
        (``__viewid__``), then delegate to the chosen operation over the
        validated items.
        """
        if not self.contexts:
            e = ViewError()
            e.principalmessage = CallViewErrorPrincipalmessage
            e.causes = CallViewViewErrorCauses
            raise e

        self.init_stepid(self.schema)
        form, reqts = self._build_form()
        form.formid = self.viewid+'_'+form.formid
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
                        validated_items = validated['items']
                        if hasattr(validated_items, 'values'):
                            # the era colander answered a mapping
                            validated_items = validated_items.values()
                        self.validated_items = list(validated_items)
                    except deform.exception.ValidationFailure as e:
                        fail = getattr(self, '%s_failure' % button.name, None)
                        if fail is None:
                            fail = self._failure
                        item = fail(e, form)
                        error = True
                    else:
                        try:
                            item = self._call_callview(button.name)
                            return item
                        except FormError as e:
                            snippet = '<div class="error">Failed: %s</div>' % e
                            self.request.sdiapi.flash(snippet, 'danger',
                                                      allow_duplicate=True)
                            item = self.adapt_item(form.render(validated), 
                                                   form.formid)
                            error = True

                    break

        if posted_formid is not None and '__viewid__' in self.request.POST:
            posted_viewid = self.request.POST['__viewid__'].split(':')
            _viewid = posted_viewid[0]
            if _viewid == self.viewid:
                self.validated_items = [get_obj(int(o)) for o  in \
                         self.request.POST['__contextsoids__'].split(':')[1:]]
                if not self.validated_items:
                    e = ViewError()
                    e.principalmessage = CallViewErrorPrincipalmessage
                    e.causes = CallViewViewErrorCauses
                    raise e

                viewname = posted_viewid[1]
                return self._call_callview(viewname)

        if item is None:
            item = self.show(form)

        if isinstance(item,dict):
            if error:
                item['isactive'] = True

            result['coordinates'] = {self.coordinates:[item]}
            result['js_links'] = reqts['js']
            result['css_links'] = reqts['css']
            result = merge_dicts(self.requirements_copy, result)
        else:
            result = item

        return result

    def _call_callview(self, viewname):
        """Re-target the chosen operation on the selected contexts and run it."""
        callview = self.validated_children[viewname]
        callview._init_children(self.validated_items)
        callview.define_executable()
        if not callview.isexecutable:
            self.isexecutable = False
            self.finished_successfully = True

        if IFormView.implementedBy(callview.view):
            callview.schema.add_idnode('__viewid__', (self.viewid+':'+viewname))
            callview.schema.add_idnode('__contextsoids__', 
                                       self._getcontextsoids())

        callview_result = callview()
        if self.isexecutable and callview.finished_successfully:
            self.finished_successfully = True
            return self.success(callview_result)

        return callview_result

    def _getcontextsoids(self):
        """The selected oids as the ``__contextsoids__`` payload."""
        result = ''
        for context in self.validated_items:
            result += ':' + str(get_oid(context))

        return result

    def success(self, validated=None):
        """Pass the operation result through."""
        return validated


def default_condition(context, request):
    """Default UI-transition condition: always True."""
    return True


class Transition(object):

    """A wizard UI transition; ``validate`` requires the matching
    transition of the *behaviour's* wizard (same id) to validate too.
    """
    def __init__(self, source, target, id, condition=(lambda x, y:True), isdefault=False):
        self.wizard = source.wizard
        self.source = source
        self.target = target
        self.source.add_outgoing(self)
        self.target.add_incoming(self)
        self.condition = condition
        self.isdefault = isdefault
        self.id = id

    def validate(self):
        """UI condition ∧ behaviour-wizard condition (when bound)."""
        behavior_transition = None
        if self.wizard.behaviorinstance is not None:
            behavior_transitions = dict(self.wizard.behaviorinstance.transitionsinstances)
            if self.id in behavior_transitions:
                behavior_transition = behavior_transitions[self.id]
                
        if behavior_transition is not None:
            return self.condition(self.wizard.context, 
                                  self.wizard.request) and \
                   behavior_transition.condition(self.wizard.context, 
                                                 self.wizard.request)

        return self.condition(self.wizard.context, self.wizard.request)


class Wizard(MultipleViewsOperation):

    """A step graph of views mirroring the dace behaviour wizard: same
    transition tuples, session-stored current step, synthetic start/end
    nodes, optional progression bar.
    """
    transitions = ()
    title = 'Wizard'
    name = 'wizard'
    durable = False # session ou pas?
    behavior = None
    informations_template = 'pontus:templates/views_templates/wizard_info.pt'
    informations_requirements = None
    include_informations = False

    def __init__(self, 
                 context, 
                 request, 
                 parent=None, 
                 wizard=None, 
                 stepid=None, 
                 **kwargs):
        super(Wizard, self).__init__(context, request, parent, 
                                     wizard, stepid, **kwargs)
        self.transitionsinstances = {}
        self.nodes = {}
        self.startnode = None
        self.endnode = None
        self.behaviorinstance = None
        if self.behavior:
            try:
                self.behavior.get_validator().validate(self.context, 
                                                       self.request)
                self.behaviorinstance = self.behavior.get_instance(
                                         self.context, self.request)
            except Exception:
                pass

        for key, view in self.views.items():
            viewinstance = view(self.context, self.request, self, self, key)
            self.nodes[key] = viewinstance

        for transition in self.transitions:
            sourceinstance = self.nodes[transition[0]]
            targetinstance = self.nodes[transition[1]]
            transitionid = transition[0]+'->'+transition[1]
            condition = None
            try:
                condition = transition[3]
            except Exception:
                condition = default_condition

            default = False
            try:
                default = transition[2]
            except Exception:
                pass

            transitioninstance = Transition(sourceinstance, targetinstance,
                                           transitionid, condition, default)
            self.transitionsinstances[transitionid] = transitioninstance

        self._add_startnode()
        self._add_endnode()
        self.currentsteps = [t.target for t in self.startnode._outgoing]

    def get_view_requirements(self):
        """The current step's requirements merged with the wizard's."""
        stepidkey = STEPID + self.viewid
        if stepidkey in self.request.session:
            self.currentsteps = [self.nodes[self.request.session.pop(stepidkey)]]

        result = self.requirements_copy
        for view in self.currentsteps:
            view_requirements = view.get_view_requirements()
            result = merge_dicts(view_requirements, result)

        return result

    def _add_startnode(self):
        """Wire a synthetic start step to every initial node."""
        initnodes = self._getinitnodes()
        self.startnode = Step(self,'start_' + self.viewid)
        for node in initnodes:
            transitionid = self.startnode.stepid+'->'+node.stepid
            self.transitionsinstances[transitionid] = Transition(
                               self.startnode, node, transitionid)

    def _add_endnode(self):
        """Wire every final node to a synthetic end step."""
        finalnodes = self._getfinalnodes()
        self.endnode = Step(self,'end_' + self.viewid)
        for node in finalnodes:
            transitionid = node.stepid+'->'+self.endnode.stepid
            self.transitionsinstances[transitionid] = Transition(
                                 node, self.endnode, transitionid)

    def _getinitnodes(self):
        """Steps without incoming transitions."""
        result = []
        for view in self.nodes.values():
            if not view._incoming:
                result.append(view)

        return result

    def _getfinalnodes(self):
        """Steps without outgoing transitions."""
        result = []
        for view in self.nodes.values():
            if not view._outgoing:
                result.append(view)

        return result

    def _count_path(self, source, target):
        """Shortest step count between two nodes (for the progression bar)."""
        nsteps = 1
        listincomming = source._incoming
        if not listincomming:
            return None

        if target in [s.source for s in listincomming]:
            return nsteps

        maxsteps = 1000
        for inct in listincomming:
            incs = self._count_path(inct.source, target)
            if incs is None:
                continue

            if incs < maxsteps:
                maxsteps = incs

        nsteps = nsteps + maxsteps
        return nsteps

    def _calculate_wizard_informations(self):
        """Current step, covered/remaining counts and percentage."""
        stepidkey = STEPID + self.viewid
        currentsteps = []
        if stepidkey in self.request.session:
            currentsteps = [self.nodes[self.request.session[stepidkey]]]

        currentstep = currentsteps[0]
        covered = self._count_path(currentstep, self.startnode)-1
        rest = self._count_path(self.endnode, currentstep)-1
        total = covered + rest
        pourcentage = covered * 100 /total
        return currentstep, total, covered, rest, pourcentage

    def getwizardinformationsview(self):
        """Render the progression bar block."""
        currentstep, total, covered, rest, pourcentage = self._calculate_wizard_informations()
        values = {'total':total, 
                  'current': covered, 
                  'title': currentstep.title, 
                  'pourcentage':pourcentage}
        body = self.content(args=values, 
                            template=self.informations_template)['body']
        result = {'body':body, 'js_links':[], 'css_links':[]}
        if self.informations_requirements is not None:
            result.update(self.informations_requirements)

        return result

    def update(self):
        """Render the current step(s); while a step finishes successfully,
        follow the first validating (non-default, else default) transition;
        reaching the end closes the wizard (``success``).
        """
        stepidkey = STEPID+self.viewid
        #TODO 
        #if stepidkey in self.request.POST:
        #    self.currentsteps = [self.viewsinstances[self.request.POST[stepidkey]]]

        if stepidkey in self.request.session:
            # resume from the stored step (mirrors the constructor)
            self.currentsteps = [
                self.nodes[self.request.session.pop(stepidkey)]]

        result = None
        finished_successfully = False
        viewinstance, finished_successfully, result = self._get_result(
                                                      self.currentsteps)
        self.isexecutable = viewinstance.isexecutable
        if viewinstance is not None and \
           finished_successfully and viewinstance._outgoing and \
           not(viewinstance._outgoing[0].target == self.endnode):
            result = None
            while(result is None and \
                  not(viewinstance._outgoing[0].target == self.endnode)):
                viewinstance.after_update()
                nextsteps = [transition.target for transition in viewinstance._outgoing \
                             if (transition.validate() and not transition.isdefault)]
                if not nextsteps:
                    nextsteps = [transition.target for transition in viewinstance._outgoing \
                                 if transition.isdefault]

                viewinstance, finished_successfully, result = self._get_result(
                                                                      nextsteps)
                self.isexecutable = viewinstance.isexecutable

        if isinstance(result, dict) and self.include_informations:
            wizardinfo = self.getwizardinformationsview()
            result = merge_dicts(result, wizardinfo, ('js_links', 'css_links'))
            for coordinates in result['coordinates']:
                item = result['coordinates'][coordinates][0]
                body = item['body']
                body = wizardinfo['body']+body
                item['body'] = body

        if finished_successfully and \
           (viewinstance._outgoing[0].target == self.endnode):
            self.finished_successfully = True
            viewinstance.after_update()
            # plain steps never write the key; the resume pop may have
            # consumed it: clean up tolerantly
            self.request.session.pop(stepidkey, None)
            if viewinstance.isexecutable:
                return self.success()

        return result

    def _get_result(self, sourceviews):
        """Update one step, or several as an ad-hoc MultipleView."""
        result = None
        if len(sourceviews) == 1:
            viewinstance = sourceviews[0]
            viewinstance.before_update()
            result = viewinstance.update()
            self.title = viewinstance.title
            if isinstance(result, dict):
                result['view'] = viewinstance

            return viewinstance, viewinstance.finished_successfully, result
        else:
            multipleviewinstance = MultipleView(self.context, self.request, 
                                                self, self)
            multipleviewinstance.validated_children = sourceviews
            multipleviewinstance.define_executable()
            multipleviewinstance.before_update()
            result = multipleviewinstance.update()
            viewinstance = None
            for source_view in sourceviews:
                if source_view.finished_successfully:
                    viewinstance = source_view
                else:
                    viewinstance = multipleviewinstance

            if isinstance(result, dict):
                result['view'] = viewinstance

            return (viewinstance, 
                    multipleviewinstance.finished_successfully, 
                    result)

    def success(self, validated=None):
        """Redirect to the context's ``@@index``."""
        return HTTPFound(
            self.request.mgmt_path(self.context, '@@index'))
