# -*- coding: utf-8 -*-


STEPID = '__stepindex__'

class Step(object):

    def __init__(self, wizard=None, index=0):
        self.wizard = wizard
        self.index = index
        self.finished_successfully = False

    def condition(self):
        return True


class Wizard(object):

    steps = ()

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.stepsinstances = []
        for i, step in enumerate(self.steps):
            self.stepsinstances.append(step(self.context, self.request, None, self, i))

    def __call__(self):
        posted_stepid = 0
        if STEPID in self.request.POST:
            posted_stepid = int(self.request.POST[STEPID])

        result = self.stepsinstances[posted_stepid]()
        self.title = self.stepsinstances[posted_stepid].title
        if self.stepsinstances[posted_stepid].finished_successfully and len(self.stepsinstances)>(posted_stepid + 1):
            posted_stepid += 1
            self.request.POST.clear()
            self.title = self.stepsinstances[posted_stepid].title
            result = self.stepsinstances[posted_stepid]()

        if isinstance(result,dict):
            result['view'] = self.stepsinstances[posted_stepid]

        return result

    def update(self):
        posted_stepid = 0
        if STEPID in self.request.POST:
            posted_stepid = int(self.request.POST[STEPID])

        result = self.stepsinstances[posted_stepid].update()
        self.title = self.stepsinstances[posted_stepid].title
        if self.stepsinstances[posted_stepid].finished_successfully and len(self.stepsinstances)>(posted_stepid + 1):
            posted_stepid += 1
            self.request.POST.clear()
            self.title = self.stepsinstances[posted_stepid].title
            return self.stepsinstances[posted_stepid].upate()

        return result

        

