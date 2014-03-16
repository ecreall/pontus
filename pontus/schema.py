from zope.interface.interface import TAGGED_DATA
import inspect
import deform
import deform.widget
import colander

from substanced.schema import Schema as SH

from pontus.file import ObjectData
from pontus.visual import VisualisableElement


class Schema(VisualisableElement,SH):

    def __init__(self, _class=None, **kwargs):
        VisualisableElement.__init__(self, **kwargs)
        SH.__init__(self,**kwargs)
        self.typ = ObjectData(_class)   

    def deserialize(self, cstruct=colander.null):
        members = dict(inspect.getmembers(self))
        if TAGGED_DATA in members and 'invariants' in members[TAGGED_DATA]:
            for invariant in members[TAGGED_DATA]['invariants']:
                invariant(self, cstruct)

        appstruct = super(Schema, self).deserialize(cstruct)
        return appstruct

    def add_idnode(self, id, value=None):
        if self.get(id) is not None:
            self.__delitem__(id)

        if value is None:
            value

        idnode = colander.SchemaNode(
                colander.String(),
                name = id,
                widget=deform.widget.HiddenWidget(),
                default=value
                )
        self.children.append(idnode)


def select(schema, mask):
    """Return a new schema with only fields included in mask.
    """
    if schema.get('_csrf_token_', None) is not None:
        mask.insert(0, '_csrf_token_')

    new_schema = schema.clone()
    new_schema.children = []
    for m in mask:
        if isinstance(m, basestring):
            node = schema.get(m)
            if node is not None:
                new_schema.add(node.clone())
        else:
            node = schema.get(m[0])
            if node is not None:
                sequencenode = node.clone()
                sequencenode.children = []
                sequencenode.add(select(node.children[0], m[1]))
                new_schema.add(sequencenode)
    return new_schema


def flatten(schemes):
    if len(schemes)==0:
        return None
    
    new_schema = schemes[0].clone()
    for schema in schemes[1:]:
        clone = schema.clone()
        new_schema.children.extend(clone.children)

    return new_schema


def schemes_sum(schemes):
    if len(schemes)==0:
        return None
    
    new_schema = Schema()
    for schema in schemes:
        clone = schema.clone()
        clone.name = clone.label
        new_schema.add(clone)

    return new_schema


def omit(schema, mask, isinternal=False):
    """Return a new schema without the fields listed in mask.
    """
    if not isinternal:
        new_schema = schema.clone()
    else:
        new_schema = schema

    for m in mask:
        if isinstance(m, basestring):
            node = new_schema.get(m)
            if node is not None:
                new_schema.children.remove(node)
        else:
            node = new_schema.get(m[0])
            if node is not None:
                omit(node.children[0], m[1], True)

    return new_schema


class VisualisableElementSchema(Schema):
    
    title = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextInputWidget()
        )

    label = colander.SchemaNode(
        colander.String(),
        widget= deform.widget.TextInputWidget()
        )

    description = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextAreaWidget(rows=10, cols=60)
        )
