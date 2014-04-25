# definition of VoirPropositionDAction process
from dace.util import utility
from dace.processinstance.activity import InfiniteCardinality, ActionType
from dace.interfaces import IProcessDefinition, IRuntime, IProcessDefinitionContainer
from dace.processdefinition.processdef import ProcessDefinition
from dace.processdefinition.activitydef import ActivityDefinition
from dace.processdefinition.transitiondef import TransitionDefinition
from dace.processdefinition.eventdef import (
    StartEventDefinition,
    EndEventDefinition,
    IntermediateCatchEventDefinition,
    ConditionalEventDefinition,
    TimerEventDefinition)
from dace.objectofcollaboration.services.processdef_container import process_definition
from dace.processinstance import workitem

from pontus.core import VisualisableElement



class WorkItemS(workitem.WorkItem):
    def start(self):
        pass

@utility(name='runtime_pd.s')
class WorkItemFactoryS(workitem.WorkItemFactory):
    factory = WorkItemS

class SeeProcesses_WorkItem(workitem.WorkItem):
    def start(self):
        pass

@utility(name='runtime_pd.processes_run')
class SeeProcesses_WorkItemFactory(workitem.WorkItemFactory):
    factory = SeeProcesses_WorkItem


class WorkItemE(workitem.WorkItem):
    def start(self):
        pass

@utility(name='runtime_pd.e')
class WorkItemFactoryE(workitem.WorkItemFactory):
    factory = WorkItemE


def relation_validationA(process, context):
    return True


def roles_validationA(process, context):
    return True


def processsecurity_validationA(process, context):
    return True


def state_validationA(process, context):
    return True


class SeeProcesses(InfiniteCardinality):

    context = IRuntime
    actionType = ActionType.automatic
    relation_validation = relation_validationA
    roles_validation = roles_validationA
    processsecurity_validation = processsecurity_validationA
    state_validation = state_validationA


@process_definition(name='runtime_pd', id='runtime_pd')
class RuntimeProcessDefinition(ProcessDefinition, VisualisableElement):
    isUnique = True

    def __init__(self, **kwargs):
        super(RuntimeProcessDefinition, self).__init__(**kwargs)
        self.title = 'Processus de gestion du runtime'
        self.description = 'Ce processus permet de gerer les processus de l\'application'

    def _init_definition(self):
        self.defineNodes(
                s = StartEventDefinition(),
                processes_run = ActivityDefinition(contexts=[SeeProcesses], 
                                                   title="Voir les processus en cours",
                                                   groups=['Voir'],
                                                   description="L'action permet de voir les processus encours"),
                e = EndEventDefinition(),
        )
        self.defineTransitions(
                TransitionDefinition('s', 'processes_run'),
                TransitionDefinition('processes_run', 'e'),
        )


class WorkItemSpdc(workitem.WorkItem):
    def start(self):
        pass

@utility(name='pdc_pd.s')
class WorkItemFactorySpdc(workitem.WorkItemFactory):
    factory = WorkItemSpdc

class SeeProcessesDef_WorkItem(workitem.WorkItem):
    def start(self):
        pass

@utility(name='pdc_pd.processes_def')
class SeeProcessesDef_WorkItemFactory(workitem.WorkItemFactory):
    factory = SeeProcessesDef_WorkItem

class WorkItemEpdc(workitem.WorkItem):
    def start(self):
        pass

@utility(name='pdc_pd.e')
class WorkItemFactoryEpdc(workitem.WorkItemFactory):
    factory = WorkItemEpdc

class SeeProcessesDef(InfiniteCardinality):

    context = IProcessDefinitionContainer
    actionType = ActionType.automatic
    relation_validation = relation_validationA
    roles_validation = roles_validationA
    processsecurity_validation = processsecurity_validationA
    state_validation = state_validationA


@process_definition(name='pdc_pd', id='pdc_pd')
class PDCProcessDefinition(ProcessDefinition, VisualisableElement):
    isUnique = True

    def __init__(self, **kwargs):
        super(PDCProcessDefinition, self).__init__(**kwargs)
        self.title = 'Processus de gestion des definitions des processus'
        self.description = 'Ce processus permet de gerer les definition des processus de l\'application'

    def _init_definition(self):
        self.defineNodes(
                s = StartEventDefinition(),
                processes_def = ActivityDefinition(contexts=[SeeProcessesDef],
                                                   title="Voir les definitions des processus",
                                                   groups=['Voir'],
                                                   description="L'action permet de voir les definition des processus"),
                e = EndEventDefinition(),
        )
        self.defineTransitions(
                TransitionDefinition('s', 'processes_def'),
                TransitionDefinition('processes_def', 'e'),
        )
