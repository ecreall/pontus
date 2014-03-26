# -*- coding: utf-8 -*-

STEPID = '__stepindex__'

class Step(object):

    isexecutable = True

    def __init__(self, wizard=None, index=None):
        self.wizard = wizard
        self.index = index
        self.finished_successfully = False
        self._outgoing = []
        self._incoming = []

    def add_outgoing(self, transition):
        self._outgoing.append(transition)

    def add_incoming(self, transition):
        self._incoming.append(transition)

    def init_stepindex(self, schema, wizard=None):
        if self.wizard is not None:
            self.wizard.request.session[STEPID+self.wizard.viewid] = self.index
            #if self.index is not None:
            #    schema.add_idnode(STEPID+self.wizard.viewid, self.index)

            #if hasattr(self, 'parent'):
            #    self.parent.init_stepindex(schema)


class Transition(object):

    def __init__(self, source, target, id, condition=(lambda x, y:True)):
        self.wizard = source.wizard
        self.source = source
        self.target = target
        self.source.add_outgoing(self)
        self.target.add_incoming(self)
        self.condition = condition
        self.id = id

    def validate(self):
        return self.condition(self.wizard.context, self.wizard.request)


class ValidationError(Exception):
    principalmessage = u""
    causes = []
    solutions = []
    type = 'danger'
    template='templates/message.pt'


class Validator(object):

    @classmethod
    def validate(cls, context, request ,args=None):
        return True


class Behavior(object):

    behaviorid = NotImplemented
    title = NotImplemented
    description = NotImplemented

    @classmethod
    def get_instance(cls, context, request, args=None):
        return cls() #raise ValidationError if no action

    @classmethod
    def get_validator(cls):
        return Validator #defaultvalidator

    def validate(self, context, request, args=None):
        return True #action instance validation

    def before_execution(self, context, request):
        pass

    def start(self, context, request, appstruct):
        pass

    def execute(self, context, request, appstruct):
        pass

    def after_execution(self, context, request):
        pass

    def redirect(self, context, request, appstruct):
        pass
