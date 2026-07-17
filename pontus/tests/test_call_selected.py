# Copyright (c) 2026 by Logikascium under licence AGPL terms
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Michaël Launay

"""Tests of the ``CallSelectedContextsViews`` batch pattern (T2c).

Characterisation in the functional harness. Pinned contracts:

- construction routes each target view to its operation (``CallView``
  for basic views, ``MergedFormsView`` when ``IFormView``), keyed by
  the underscored title, with one deform button per target
  (name = underscored title, title = capitalised);
- ``_init_children`` builds a per-target SUBCLASS of the operation
  classes (fixed 2026-07-17: the shared classes are no longer
  mutated);
- the base ``ViewOperation`` protocol CALLS ``contexts()`` and stores
  the result on the instance (a method, not a property);
- the selection widget renders each context through ``get_view``;
- an empty selection raises ``ViewError`` — both at ``update()`` entry
  and on an empty ``__contextsoids__`` round-trip;
- the ``__viewid__`` round-trip delegates end to end: the target
  behaviour executes once per selected context;
- a malformed selection post lands in the validation-failure branch:
  nothing executes and the re-rendered form is flagged ``isactive``;
- a VALID button selection completes end to end (fixed 2026-07-17:
  the validated set is consumed as such).
"""
from dace.objectofcollaboration.object import Object

from substanced.util import get_oid

from pyramid_layout.layout import Structure

from pontus.core import VisualisableElement
from pontus.testing import FunctionalTests
from pontus.view import ViewError
from pontus.view_operation import (
    CallSelectedContextsViews, CallView, MergedFormsView)
from pontus.tests.example.app import ViewA, FormViewA


class SelObject(VisualisableElement, Object):
    def get_view(self, request, template=None):
        # production snippets are layout Structures (not escaped)
        return Structure('<i>%s</i>' % self.title)


class Batch(CallSelectedContextsViews):
    name = 'batch'
    views = [ViewA, FormViewA]

    def contexts(self):
        return getattr(self.request, '_batch_contexts', [])


class TestCallSelectedContextsViews(FunctionalTests):

    def setUp(self):
        super(TestCallSelectedContextsViews, self).setUp()
        self.request.validationA = True
        self.request.viewexecuted = []
        self.obj_a = SelObject(title='sel_a')
        self.obj_b = SelObject(title='sel_b')
        self.app['sel_a'] = self.obj_a
        self.app['sel_b'] = self.obj_b
        self.request._batch_contexts = [self.obj_a, self.obj_b]

    def test_construction_routes_and_buttons(self):
        batch = Batch(self.app, self.request)
        self.assertEqual(batch.buttons, ['ViewA', 'FormView A'])
        self.assertIsInstance(batch.validated_children['ViewA'], CallView)
        self.assertIsInstance(batch.validated_children['FormView_A'],
                              MergedFormsView)
        form, _ = batch._build_form()
        self.assertEqual([(b.name, b.title) for b in form.buttons],
                         [('ViewA', 'Viewa'), ('FormView_A', 'Formview a')])

    def test_construction_leaves_the_operation_classes_untouched(self):
        """FIXED (2026-07-17, was the pinned design smell): the
        children are per-target subclasses — the shared operation
        classes are no longer mutated."""
        titles_before = (CallView.title, MergedFormsView.title)
        batch = Batch(self.app, self.request)
        self.assertEqual((CallView.title, MergedFormsView.title),
                         titles_before)
        # the children still carry their target configuration
        self.assertEqual(batch.validated_children['ViewA'].title,
                         'ViewA')
        self.assertEqual(batch.validated_children['FormView_A'].title,
                         'FormView A')

    def test_contexts_protocol_is_a_call(self):
        batch = Batch(self.app, self.request)
        # ViewOperation called contexts() and stored the list
        self.assertEqual(batch.contexts, [self.obj_a, self.obj_b])

    def test_empty_contexts_raise(self):
        self.request._batch_contexts = []
        batch = Batch(self.app, self.request)
        self.assertRaises(ViewError, batch.update)

    def test_selection_form_renders(self):
        batch = Batch(self.app, self.request)
        result = batch.update()
        self.assertEqual(sorted(result),
                         ['coordinates', 'css_links', 'js_links'])
        body = result['coordinates'][batch.coordinates][0]['body']
        self.assertIn('checkbox', body)
        self.assertIn('<i>sel_a</i>', body)
        self.assertIn('<i>sel_b</i>', body)

    def test_viewid_roundtrip_delegates_end_to_end(self):
        batch = Batch(self.app, self.request)
        self.request.POST = {
            '__formid__': 'other',
            '__viewid__': batch.viewid + ':ViewA',
            '__contextsoids__': ':%s:%s' % (get_oid(self.obj_a),
                                            get_oid(self.obj_b)),
        }
        result = batch.update()
        self.assertIsInstance(result, dict)
        self.assertIs(batch.finished_successfully, True)
        # the target behaviour ran once per selected context
        self.assertEqual(self.request.viewexecuted,
                         ['behaviorA', 'behaviorA'])

    def test_viewid_roundtrip_empty_selection_raises(self):
        batch = Batch(self.app, self.request)
        self.request.POST = {
            '__formid__': 'other',
            '__viewid__': batch.viewid + ':ViewA',
            '__contextsoids__': '',
        }
        self.assertRaises(ViewError, batch.update)
        # brittle parsing pinned: a lone ':' payload dies on int('')
        self.request.POST['__contextsoids__'] = ':'
        self.assertRaises(ValueError, batch.update)

    def test_button_post_without_structure_fails_validation(self):
        batch = Batch(self.app, self.request)
        form, _ = batch._build_form()
        form.formid = batch.viewid + '_' + form.formid
        self.request.POST = {
            '__formid__': form.formid,
            'ViewA': 'ViewA',
            'items': str(get_oid(self.obj_a)),
        }
        result = batch.update()
        self.assertEqual(batch.validated_items, [])
        self.assertEqual(self.request.viewexecuted, [])
        item = result['coordinates'][batch.coordinates][0]
        self.assertIs(item.get('isactive'), True)

    def test_button_post_valid_selection(self):
        """FIXED (2026-07-17, was latent bug #3): the validated
        selection is consumed as a set OR a mapping — the direct
        button path now completes end to end."""
        batch = Batch(self.app, self.request)
        form, _ = batch._build_form()
        form.formid = batch.viewid + '_' + form.formid
        self.request.POST = {
            '__formid__': form.formid,
            'ViewA': 'ViewA',
            '_csrf_token_': self.request.session.get_csrf_token(),
            '__start__': 'items:sequence',
            'checkbox': str(get_oid(self.obj_a)),
            '__end__': 'items:sequence',
        }
        result = batch.update()
        self.assertEqual(batch.validated_items, [self.obj_a])
        self.assertEqual(self.request.viewexecuted, ['behaviorA'])
        self.assertIs(batch.finished_successfully, True)
        self.assertIsInstance(result, dict)

    def test_getcontextsoids_format(self):
        batch = Batch(self.app, self.request)
        batch.validated_items = [self.obj_a, self.obj_b]
        self.assertEqual(
            batch._getcontextsoids(),
            ':%s:%s' % (get_oid(self.obj_a), get_oid(self.obj_b)))
