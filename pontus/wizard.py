# -*- coding: utf-8 -*-


STEPID = '__stepindex__'

class Step(object):

    def __init__(self, wizard = None, index = 0):
        self.wizard = wizard
        self.index = index
        self.esucces = False

    def condition(self):
        return True


class Wizard(object):

    steps = ()

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.stepsinstances = []
        i = 0
        for step in self.steps:
            self.stepsinstances.append(step(self.context, self.request, self, i))
            i+=1

    def __call__(self):
        posted_stepid = 0
        if STEPID in self.request.POST:
            posted_stepid = int(self.request.POST[STEPID])

        result = self.stepsinstances[posted_stepid]()
        self.title = self.stepsinstances[posted_stepid].title
        if self.stepsinstances[posted_stepid].esucces and len(self.stepsinstances)>(posted_stepid + 1):
            posted_stepid += 1
            self.request.POST.clear()
            self.title = self.stepsinstances[posted_stepid].title
            return self.stepsinstances[posted_stepid]()
        else:
            return result
        

