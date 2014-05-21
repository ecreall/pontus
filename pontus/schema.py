from zope.interface.interface import TAGGED_DATA
import inspect
import deform
import deform.widget
import colander

from substanced.schema import Schema as SH

from pontus.file import ObjectData, ObjectOID, OBJECT_DATA

try:
      basestring
except NameError:
      basestring = str


def omit_nodes(schemanode, omit):
    for o in omit:
        if isinstance(o, basestring):
            node = schemanode.get(o, None)
            if node is not None:
                node.to_omit = True 
        else:
            node = schemanode.get(o[0])
            if node is not None:
                omit_nodes(node.children[0], o[1])


class Schema(SH):

    title = ''
    label = ''
    description = ''

    def __init__(self, objectfactory=None, editable=False, omit=(),**kwargs):
        SH.__init__(self,**kwargs)
        self.typ = ObjectData(objectfactory, editable)
        if editable or objectfactory is not None:
            self._omit_nodes(omit)

        if editable:
            self.add_idnode(ObjectOID)

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

        if value is None:
            value

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
                sequencenode = node.clone()
                sequencenode.children = []
                sequencenode.add(select(node.children[0], m[1]))
                new_schema.add(sequencenode)
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
            if node is not None:
                omit(node.children[0], m[1], True)

    return new_schema
