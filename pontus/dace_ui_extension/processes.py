# definition of VoirPropositionDAction process
from dace.util import utility
from dace.processinstance.activity import InfiniteCardinality, ActionType
from dace.interfaces import IProcessDefinition, IRuntime, IProcessDefinitionContainer, IProcess
from dace.processdefinition.processdef import ProcessDefinition
from dace.processdefinition.activitydef import ActivityDefinition
from dace.processdefinition.transitiondef import TransitionDefinition
from dace.processdefinition.eventdef import (
    StartEventDefinition,
    EndEventDefinition,
    IntermediateCatchEventDefinition,
    ConditionalEventDefinition,
    TimerEventDefinition)
from dace.processdefinition.gatewaydef import ParallelGatewayDefinition, ExclusiveGatewayDefinition
from dace.objectofcollaboration.services.processdef_container import process_definition

from pontus.core import VisualisableElement




def relation_validationA(process, context):
    return True


def roles_validationA(process, context):
    return True


def processsecurity_validationA(process, context):
    return True


def state_validationA(process, context):
    return True


class StatisticProcesses(InfiniteCardinality):

    context = IRuntime
    actionType = ActionType.automatic
    relation_validation = relation_validationA
    roles_validation = roles_validationA
    processsecurity_validation = processsecurity_validationA
    state_validation = state_validationA


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
                pg = ParallelGatewayDefinition(),
                processes_run = ActivityDefinition(contexts=[SeeProcesses], 
                                                   title="Voir les processus en cours",
                                                   groups=['Voir'],
                                                   description="L'action permet de voir les processus encours"),
                processes_stat = ActivityDefinition(contexts=[StatisticProcesses],
                                                   title="Voir les statistiques",
                                                   groups=['Voir'],
                                                   description="L'action permet de voir les statistiques des processus en cours"),
                eg = ExclusiveGatewayDefinition(),
                e = EndEventDefinition(),
        )
        self.defineTransitions(
                TransitionDefinition('s', 'pg'),
                TransitionDefinition('pg', 'processes_run'),
                TransitionDefinition('processes_run', 'eg'),
                TransitionDefinition('pg', 'processes_stat'),
                TransitionDefinition('processes_stat', 'eg'),
                TransitionDefinition('eg', 'e'),
        )


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
        self.title = 'Processus de gestion du containeur des definitions des processus'
        self.description = 'Ce processus permet de gerer le containeur des definition des processus de l\'application'

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


class SeeProcessDef(InfiniteCardinality):

    context = IProcessDefinition
    actionType = ActionType.automatic
    relation_validation = relation_validationA
    roles_validation = roles_validationA
    processsecurity_validation = processsecurity_validationA
    state_validation = state_validationA


class StatisticProcessesDef(InfiniteCardinality):

    context = IProcessDefinition
    actionType = ActionType.automatic
    relation_validation = relation_validationA
    roles_validation = roles_validationA
    processsecurity_validation = processsecurity_validationA
    state_validation = state_validationA

class InstanceProcessesDef(InfiniteCardinality):

    context = IProcessDefinition
    actionType = ActionType.automatic
    relation_validation = relation_validationA
    roles_validation = roles_validationA
    processsecurity_validation = processsecurity_validationA
    state_validation = state_validationA


@process_definition(name='pd_pd', id='pd_pd')
class PDProcessDefinition(ProcessDefinition, VisualisableElement):
    isUnique = True

    def __init__(self, **kwargs):
        super(PDProcessDefinition, self).__init__(**kwargs)
        self.title = 'Processus de gestion des definitions des processus'
        self.description = 'Ce processus permet de gerer les definition des processus de l\'application'

    def _init_definition(self):
        self.defineNodes(
                s = StartEventDefinition(),
                pg = ParallelGatewayDefinition(),
                processes_def = ActivityDefinition(contexts=[SeeProcessDef],
                                                   title="Voir la definition de processus",
                                                   groups=['Voir'],
                                                   description="L'action permet de voir les details de la definition de processus"),
                processes_stat = ActivityDefinition(contexts=[StatisticProcessesDef],
                                                   title="Voir les statistiques",
                                                   groups=['Voir'],
                                                   description="L'action permet de voir les statistiques des processus en cours"),

                processes_run = ActivityDefinition(contexts=[InstanceProcessesDef],
                                                   title="Voir les processus en cours",
                                                   groups=['Voir'],
                                                   description="L'action permet de voir les details des processus en cours"),
                eg = ExclusiveGatewayDefinition(),
                e = EndEventDefinition(),
        )
        self.defineTransitions(
                TransitionDefinition('s', 'pg'),
                TransitionDefinition('pg', 'processes_def'),
                TransitionDefinition('pg', 'processes_stat'),
                TransitionDefinition('pg', 'processes_run'),
                TransitionDefinition('processes_def', 'eg'),
                TransitionDefinition('processes_run', 'eg'),
                TransitionDefinition('processes_stat', 'eg'),
                TransitionDefinition('eg', 'e'),
        )



class SeeProcess(InfiniteCardinality):

    context = IProcess
    actionType = ActionType.automatic
    relation_validation = relation_validationA
    roles_validation = roles_validationA
    processsecurity_validation = processsecurity_validationA
    state_validation = state_validationA


class StatisticProcess(InfiniteCardinality):

    context = IProcess
    actionType = ActionType.automatic
    relation_validation = relation_validationA
    roles_validation = roles_validationA
    processsecurity_validation = processsecurity_validationA
    state_validation = state_validationA


@process_definition(name='p_pd', id='p_pd')
class PProcessDefinition(ProcessDefinition, VisualisableElement):
    isUnique = True

    def __init__(self, **kwargs):
        super(PProcessDefinition, self).__init__(**kwargs)
        self.title = 'Processus de gestion des processus'
        self.description = 'Ce processus permet de gerer les processus de l\'application'

    def _init_definition(self):
        self.defineNodes(
                s = StartEventDefinition(),
                pg = ParallelGatewayDefinition(),
                processes_def = ActivityDefinition(contexts=[SeeProcess],
                                                   title="Voir le processus",
                                                   groups=['Voir'],
                                                   description="L'action permet de voir les details du processus"),
                processes_stat = ActivityDefinition(contexts=[StatisticProcess],
                                                   title="Voir les statistiques",
                                                   groups=['Voir'],
                                                   description="L'action permet de voir les statistiques du processus en cours"),
                eg = ExclusiveGatewayDefinition(),
                e = EndEventDefinition(),
        )
        self.defineTransitions(
                TransitionDefinition('s', 'pg'),
                TransitionDefinition('pg', 'processes_def'),
                TransitionDefinition('pg', 'processes_stat'),
                TransitionDefinition('processes_def', 'eg'),
                TransitionDefinition('processes_stat', 'eg'),
                TransitionDefinition('eg', 'e'),
        )
