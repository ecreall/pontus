# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

from zope.interface.interface import TAGGED_DATA
import inspect
import deform
import deform.widget
import colander

from substanced.schema import Schema as OriginSchema

from pontus.file import ObjectData, OBJECT_OID

try:
    basestring
except NameError:
    basestring = str


def omit_nodes(schemanode, omit):
    for o in omit:
        if isinstance(o, basestring):
            node = schemanode.get(o, None)
            if node is not None:
                newnode = node.clone()
                index = schemanode.children.index(node)
                newnode.to_omit = True
                schemanode.insert(index, newnode)
                schemanode.children.remove(node)
        else:
            node = schemanode.get(o[0])
            if type(node) == colander.SchemaNode:
                node = node.children[0]

            if node is not None:
                omit_nodes(node, o[1])


class Schema(OriginSchema):

    title = ''
    label = ''
    description = ''
    typ_factory = ObjectData

    def __init__(self, factory=None, editable=False, omit=(),**kwargs):
        OriginSchema.__init__(self,**kwargs)
        self.typ = self.typ_factory(factory, editable)
        if editable or factory is not None:
            self._omit_nodes(omit)

        if editable:
            self.add_idnode(OBJECT_OID)

    def _omit_nodes(self, omit):
        csrf = self.get('_csrf_token_', None)
        if csrf is not None:
            csrf.to_omit = True
            csrf.private = True

        omit_nodes(self, omit)

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

        idnode = colander.SchemaNode(
                colander.String(),
                name = id,
                widget=deform.widget.HiddenWidget(),
                default=value
                )
        idnode.to_omit = True
        idnode.private = True
        self.children.append(idnode)


def select(schema, mask):
    """Return a new schema with only fields included in mask.
    """
    for n in schema.children:
        if getattr(n, 'private', False):
            mask.insert(0, n.name)

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
                if type(node) == colander.SchemaNode:
                    sequencenode = node.clone()
                    node = node.children[0]
                    sequencenode.children = []
                    sequencenode.add(select(node, m[1]))
                    new_schema.add(sequencenode)
                else:
                    new_schema.add(select(node, m[1]))

    return new_schema


def flatten(schemes):
    if len(schemes) == 0:
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
            if type(node) == colander.SchemaNode:
                node = node.children[0]

            if node is not None:
                omit(node, m[1], True)

    return new_schema
