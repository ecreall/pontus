# Copyright (c) 2026 by Logikascium under licence AGPL terms
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Michaël Launay

"""Unit-level tests of the pontus widgets (T2, first batch).

Characterisation in the functional harness (the widgets resolve posted
oids to real objects through the objectmap, and the deform renderer is
wired by the application). Pinned contracts:

- the Select family resolves oid-strings to OBJECTS and passes other
  strings through; ``multiple=True`` is required for list pstructs
  (deform 3 base contract); an empty list deserializes to ``null``;
- ``RadioChoiceWidget`` (single) takes the FIRST element of a posted
  list; ``CheckboxChoiceWidget`` always answers a tuple;
- ``FileWidget`` collects its tmpstore on the root form (cleanup
  hook), honours ``_object_removed`` and answers
  ``{'__objectoid__': oid}`` when only the reference was posted and
  the referenced object has no ``fp``;
- ``ImageWidget`` parses the crop floats with safe defaults
  (x/y 10.0, r 0.0, area 100.0);
- ``SequenceWidget.deserialize`` keeps the parented subfields
  (``sequence_fields``, parent weakref) and aggregates ``Invalid``;
- ``Length`` raises with HALF-interpolated messages: ``str.format``
  substitutes the braces inside ``${min}`` and leaves the dollar —
  the message ends in ``$3``/``$5`` (the historical quirk is part of
  the contract).
"""
import colander
import deform
from colander import Invalid, null

from substanced.util import get_oid

from dace.util import get_obj

from pontus.testing import FunctionalTests
from pontus import widget as pontus_widget


class TestWidgets(FunctionalTests):

    def setUp(self):
        super(TestWidgets, self).setUp()
        self.root = self.app
        self.users = self.app['principals']['users']
        self.field = deform.Field(colander.SchemaNode(colander.String()))

    # --- pure helpers -------------------------------------------------

    def test_memory_tmp_store(self):
        store = pontus_widget.MemoryTmpStore()
        store['name'] = {'fp': None}
        self.assertIsNone(store.preview_url('name'))
        self.assertEqual(store['name'], {'fp': None})

    def test_length_validator(self):
        _ = lambda msg: msg
        validator = pontus_widget.Length(_, min=3, max=5)
        node = colander.SchemaNode(colander.String())
        validator(node, 'abc')          # within range: no raise
        with self.assertRaises(Invalid) as ctx:
            validator(node, 'ab')
        # '${min}'.format(min=3): the braces interpolate, the dollar
        # stays — the historical message ends in '$3'
        self.assertEqual(ctx.exception.msg,
                         'Shorter than minimum length $3')
        with self.assertRaises(Invalid) as ctx:
            validator(node, 'abcdef')
        self.assertEqual(ctx.exception.msg,
                         'Longer than maximum length $5')

    # --- the Select family --------------------------------------------

    def test_select_deserialize_scalar(self):
        widget = pontus_widget.SelectWidget(values=[])
        self.assertEqual(widget.deserialize(self.field, 'abc'), 'abc')
        self.assertIs(
            widget.deserialize(self.field, str(get_oid(self.users))),
            self.users)
        self.assertIs(widget.deserialize(self.field, null), null)
        self.assertIs(widget.deserialize(self.field, ''), null)

    def test_select_deserialize_multiple(self):
        widget = pontus_widget.SelectWidget(values=[], multiple=True)
        result = widget.deserialize(
            self.field, ['abc', str(get_oid(self.root))])
        self.assertEqual(result[0], 'abc')
        self.assertIs(result[1], self.root)
        self.assertIs(widget.deserialize(self.field, []), null)

    def test_radio_choice_deserialize(self):
        widget = pontus_widget.RadioChoiceWidget(values=[])
        # single widget: a posted list collapses to its first element
        self.assertEqual(widget.deserialize(self.field, ['x', 'y']), 'x')
        self.assertIs(
            widget.deserialize(self.field, str(get_oid(self.users))),
            self.users)
        self.assertIs(widget.deserialize(self.field, null), null)

    def test_checkbox_choice_deserialize(self):
        widget = pontus_widget.CheckboxChoiceWidget(values=[])
        self.assertEqual(widget.deserialize(self.field, 'zz'), ('zz',))
        result = widget.deserialize(
            self.field, ['abc', str(get_oid(self.users))])
        self.assertEqual(result[0], 'abc')
        self.assertIs(result[1], self.users)
        self.assertIsInstance(result, tuple)
        self.assertIs(widget.deserialize(self.field, null), null)

    # --- files and images ---------------------------------------------

    def test_file_widget_deserialize(self):
        store = pontus_widget.MemoryTmpStore()
        widget = pontus_widget.FileWidget(tmpstore=store)
        form = deform.Form(colander.SchemaNode(colander.Mapping()))
        self.assertIs(
            widget.deserialize(form, {'_object_removed': 'true'}), null)
        # the tmpstore is collected on the root form (cleanup hook)
        self.assertEqual(form.stores, [store])
        form = deform.Form(colander.SchemaNode(colander.Mapping()))
        self.assertIs(widget.deserialize(form, {}), null)
        form = deform.Form(colander.SchemaNode(colander.Mapping()))
        oid = str(get_oid(self.users))
        # referenced object without ``fp``: the reference alone answers
        self.assertEqual(widget.deserialize(form, {'__objectoid__': oid}),
                         {'__objectoid__': oid})

    def test_image_widget_crop_defaults(self):
        store = pontus_widget.MemoryTmpStore()
        widget = pontus_widget.ImageWidget(tmpstore=store)
        form = deform.Form(colander.SchemaNode(colander.Mapping()))
        oid = str(get_oid(self.users))
        result = widget.deserialize(
            form, {'__objectoid__': oid, 'y': '2.5', 'r': 'oops'})
        self.assertEqual(result['x'], 10.0)         # default
        self.assertEqual(result['y'], 2.5)          # parsed
        self.assertEqual(result['r'], 0.0)          # ValueError -> default
        self.assertEqual(result['area_height'], 100.0)
        self.assertEqual(result['area_width'], 100.0)

    # --- sequences ----------------------------------------------------

    def _sequence_field(self, item_type):
        schema = colander.SchemaNode(colander.Mapping())
        schema.add(colander.SchemaNode(
            colander.Sequence(),
            colander.SchemaNode(item_type, name='item'),
            name='seq', widget=pontus_widget.SequenceWidget()))
        form = deform.Form(schema)
        return form['seq']

    def test_sequence_deserialize_keeps_parented_subfields(self):
        field = self._sequence_field(colander.String())
        result = field.widget.deserialize(field, ['a', 'b'])
        self.assertEqual(result, ['a', 'b'])
        self.assertEqual(len(field.sequence_fields), 2)
        for subfield, value in zip(field.sequence_fields, ['a', 'b']):
            self.assertEqual(subfield.cstruct, value)
            self.assertIs(subfield.parent, field.children[0].parent)

    def test_sequence_deserialize_child_failure(self):
        # a widget-level child failure (mapping fed a non-dict) is NOT
        # aggregated on this deform-3 path: the child's Invalid
        # propagates as-is, and ``sequence_fields`` keeps only the
        # successfully processed items — the observed contract
        schema = colander.SchemaNode(colander.Mapping())
        item = colander.SchemaNode(colander.Mapping(), name='item')
        item.add(colander.SchemaNode(colander.String(), name='inner'))
        schema.add(colander.SchemaNode(
            colander.Sequence(), item, name='seq',
            widget=pontus_widget.SequenceWidget()))
        field = deform.Form(schema)['seq']
        with self.assertRaises(Invalid) as ctx:
            field.widget.deserialize(
                field, [{'inner': 'a'}, 'notadict'])
        self.assertIn('is not a mapping type', ctx.exception.msg)
        self.assertIsNone(ctx.exception.value)
        self.assertEqual(ctx.exception.children, [])
        self.assertEqual(len(field.sequence_fields), 1)
        self.assertEqual(field.sequence_fields[0].cstruct,
                         {'inner': 'a'})

    # --- serialize smoke (the renderer is wired by the app) -----------

    def _widget_field(self, widget):
        # templates read field.widget.*: the widget must live on the
        # field's schema (canonical deform wiring)
        return deform.Field(colander.SchemaNode(colander.String(),
                                                widget=widget))

    def test_serialize_smoke(self):
        users_oid = str(get_oid(self.users))
        radio = pontus_widget.RadioChoiceWidget(
            values=[(users_oid, 'The users')])
        html = radio.serialize(self._widget_field(radio), users_oid)
        self.assertIn('__start__', html)
        self.assertIn('The users', html)
        checkbox = pontus_widget.CheckboxChoiceWidget(
            values=[(users_oid, 'The users')])
        html = checkbox.serialize(self._widget_field(checkbox),
                                  (users_oid,))
        self.assertIn('checkbox', html)
        select = pontus_widget.SelectWidget(
            values=[(users_oid, 'The users')])
        html = select.serialize(self._widget_field(select), users_oid)
        self.assertIn('<select', html)
        self.assertIn('The users', html)
