import re
from substanced.sdi import mgmt_view
from substanced.sdi import LEFT

from dace.objectofcollaboration.runtime import Runtime
from dace.objectofcollaboration.services.processdef_container import ProcessDefinitionContainer
from dace.processdefinition.processdef import ProcessDefinition
from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from dace.processinstance.process import Process

from .processes import (
           SeeProcessesDef, 
           SeeProcesses, 
           StatisticProcessesDef, 
           SeeProcessDef, 
           InstanceProcessesDef, 
           StatisticProcesses, 
           SeeProcess, 
           StatisticProcess,
           SeeProcessDatas,
           DoActivitiesProcess)
from pontus.view import BasicView



@mgmt_view(
    name = 'Processes',
    context=Runtime,
    renderer='pontus:templates/view.pt'
    )
class RuntimeView(BasicView):

    title = 'Processes'
    self_template = 'pontus:dace_ui_extension/templates/runtime_view.pt'
    viewid = 'processes'
    name='Processes'
    #coordinates = 'left'
    behaviors = [SeeProcesses]

    def _processes(self, processes):
        processes.sort()
        allprocesses = []
        nb_encours = 0
        nb_bloque = 0
        nb_termine = 0
       
        for p in processes:
            bloced = not [w for w in p.getWorkItems().values() if w.validate()]
            processe = {'url':self.request.mgmt_path(p, '@@index'), 'process':p, 'bloced':bloced}
            allprocesses.append(processe)
            if p._finished:
                nb_termine += 1
            elif bloced:
                nb_bloque += 1
            else:
                nb_encours += 1

        return nb_encours, nb_bloque, nb_termine, allprocesses

    def _update(self, processes):
        result = {}
        nb_encours, nb_bloque, nb_termine, allprocesses = self._processes(processes)
        values = {'processes': allprocesses, 
                  'encours':nb_encours,
                  'bloque':nb_bloque,
                  'termine':nb_termine}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result

    def update(self):
        self.execute(None)
        result = self._update(self.context.processes)
        return result


@mgmt_view(
    name = 'StatisticRun',
    context=Runtime,
    renderer='pontus:templates/view.pt'
    )
class ProcessStatisticView(BasicView):

    title = 'Statistic'
    self_template = 'pontus:dace_ui_extension/templates/runtimeprocesses_statistic_view.pt'
    viewid = 'statistic'
    name='StatisticRun'
    coordinates = 'left'
    behaviors = [StatisticProcesses]

    def _values(self, processes):
        runtime_view = RuntimeView(self.context, self.request)
        nb_encours, nb_bloque, nb_termine, allprocesses =  runtime_view._processes(processes)
        blocedprocesses = [p['process'] for p in  allprocesses if p['bloced'] and not p['process']._finished ]
        terminetedprocesses = [ p['process'] for p in  allprocesses if p['process']._finished]
        activeprocesses = [ p['process'] for p in  allprocesses if  not p['process']._finished and not p['bloced']]

        result_bloced_runtime_v = runtime_view._update(blocedprocesses)
        item = result_bloced_runtime_v['coordinates'][runtime_view.coordinates][0]
        bloquesBody =item['body']

        result_encours_runtime_v = runtime_view._update(activeprocesses)
        item = result_encours_runtime_v['coordinates'][runtime_view.coordinates][0]
        encoursBody =item['body']

        result_termines_runtime_v = runtime_view._update(terminetedprocesses)
        item = result_termines_runtime_v['coordinates'][runtime_view.coordinates][0]
        terminesBody =item['body']
        values = {'encours':nb_encours,
                  'bloque':nb_bloque,
                  'termine':nb_termine,
                  'terminesBody':terminesBody,
                  'encoursBody':encoursBody,
                  'bloquesBody':bloquesBody
                }
        return values
        

    def update(self):
        self.execute(None)
        result = {}
        values = self._values(self.context.processes)   
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


@mgmt_view(
    name = 'ProcessesDef',
    context=ProcessDefinitionContainer,
    renderer='pontus:templates/view.pt'
    )
class ProcessDefinitionContainerView(BasicView):

    title = 'Processes'
    self_template = 'pontus:dace_ui_extension/templates/defcontainer_view.pt'
    viewid = 'processes'
    name='ProcessesDef'
    #coordinates = 'left'
    behaviors = [SeeProcessesDef]

    def _processes(self):
        from pontus.panels import NavBarPanel
        processes = self.context.definitions
        processes.sort()
        allprocesses = []
        for p in processes:
            nav_bar = NavBarPanel(p, self.request)
            actions = nav_bar()
            processe = {'url':self.request.mgmt_path(p, '@@index'), 'process':p, 'nav_bar':actions}
            allprocesses.append(processe) 

        return allprocesses

    def update(self):
        self.execute(None)
        result = {}
        values = {'processes': self._processes()}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


@mgmt_view(
    name = 'StatisticDef',
    context=ProcessDefinition,
    renderer='pontus:templates/view.pt'
    )
class ProcessDefinitionStatisticView(BasicView):

    title = 'Statistic'
    self_template = 'pontus:dace_ui_extension/templates/processdef_statistic_view.pt'
    viewid = 'statistic'
    name='StatisticDef'
    coordinates = 'left'
    behaviors = [StatisticProcessesDef]

    def update(self):
        self.execute(None)
        result = {}
        values = ProcessStatisticView(self.context, self.request)._values(self.context.started_processes)
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


@mgmt_view(
    name = 'ProcessDef',
    context=ProcessDefinition,
    renderer='pontus:templates/view.pt'
    )
class ProcessDefinitionView(BasicView):

    title = 'La definition du processus'
    self_template = 'pontus:dace_ui_extension/templates/processdef_view.pt'
    viewid = 'processdef'
    name='ProcessDef'
    #coordinates = 'left'
    behaviors = [SeeProcessDef]

    def update(self):
        self.execute(None)
        result = {}
        values = {'processdef': self.context}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


@mgmt_view(
    name = 'ProcessInst',
    context=ProcessDefinition,
    renderer='pontus:templates/view.pt'
    )
class ProcessesPDDefinitionView(BasicView):

    title = 'Les instance de la definition'
    self_template = 'pontus:dace_ui_extension/templates/processinstances_view.pt'
    viewid = 'processinstances'
    name='ProcessInst'
    #coordinates = 'left'
    behaviors = [InstanceProcessesDef]

    def _processes(self):
        processes = self.context.started_processes
        processes.sort()
        allprocesses = []
        for p in processes:
            processe = {'url':self.request.mgmt_path(p, '@@index'), 'process':p}
            allprocesses.append(processe) 

        return allprocesses

    def update(self):
        self.execute(None)
        result = {}
        values = {'processes': self._processes(),
                   'p_id': self.context.title}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


@mgmt_view(
    name = 'Process',
    context=Process,
    renderer='pontus:templates/view.pt'
    )
class ProcessView(BasicView):

    title = 'Les detail du processus'
    self_template = 'pontus:dace_ui_extension/templates/process_view.pt'
    viewid = 'process'
    name='Process'
    #coordinates = 'left'
    behaviors = [SeeProcess]

    def _actions(self):
        definition = self.context.definition
        definition_actions = definition.actions #les action du group Voir @TODO !
        definition_actions.sort()
        alldefinitions_actions = []
        for a in definition_actions:
           view = DEFAULTMAPPING_ACTIONS_VIEWS[a.action._class]
           view_instance = view(definition, self.request) 
           view_result = view_instance.update()
           body = view_result['coordinates'][view.coordinates][0]['body']
           alldefinitions_actions.append({'body':body, 'action':a.action})

        return alldefinitions_actions

    def update(self):
        self.execute(None)
        result = {}
        values = {'actions': self._actions()}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


@mgmt_view(
    name = 'Statistic',
    context=Process,
    renderer='pontus:templates/view.pt'
    )
class StatisticProcessView(BasicView):

    title = 'Statistic'
    self_template = 'pontus:dace_ui_extension/templates/processstatistic_view.pt'
    viewid = 'Statistic'
    name='Statistic'
    coordinates = 'left'
    behaviors = [StatisticProcess]

    def _actions(self):
        allactions = {}
        return allactions

    def update(self):
        self.execute(None)
        result = {}
        values = {'actions': self._actions()}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


@mgmt_view(
    name = 'Les donnees manipulees',
    context=Process,
    renderer='pontus:templates/view.pt'
    )
class ProcessDataView(BasicView):

    title = 'Les donnees manipulees'
    self_template = 'pontus:dace_ui_extension/templates/processdatas_view.pt'
    viewid = 'processdata'
    name='Les donnees manipulees'
    #coordinates = 'left'
    behaviors = [SeeProcessDatas]

    def _involved_datas(self):
        datas = self.context.execution_context.all_involveds()
        alldatas = []
        for d in datas:
            alldatas.append({'url':self.request.mgmt_path(d, '@@index'), 'data':d})

        return alldatas

    def update(self):
        self.execute(None)
        result = {}
        values = {'datas': self._involved_datas()}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


@mgmt_view(
    name = 'Les actions a realiser',
    context=Process,
    renderer='pontus:templates/view.pt'
    )
class DoActivitiesProcessView(BasicView):

    title = 'Les actions a realiser'
    self_template = 'pontus:dace_ui_extension/templates/processactions_view.pt'
    viewid = 'processactions'
    name='Les actions a realiser'
    #coordinates = 'left'
    behaviors = [DoActivitiesProcess]

    def _actions(self):
        datas = self.context.execution_context.all_involveds()
        all_actions = []
        resources = {}
        resources['js_links'] = []
        resources['css_links'] = []
        for d in datas:
            p_actions = [(d,a) for a in d.actions if a.action.process is self.context]
            all_actions.extend(p_actions)

        all_actions.sort()
        allbodies_actions = []
        for t in all_actions:
           a = t[1]
           c = t[0]
           view = DEFAULTMAPPING_ACTIONS_VIEWS[a.action._class]
           view_instance = view(c, self.request, behaviors=[a.action])
           view_result = view_instance()
           if isinstance(view_result, dict):
               body = view_result['coordinates'][view.coordinates][0]['body']
               allbodies_actions.append({'body':body, 'action':a.action})
               resources['js_links'].extend(view_result['js_links'])
               resources['css_links'].extend(view_result['css_links'])

        return resources, allbodies_actions

    def update(self):
        self.execute(None)
        result = {}
        resources, actions = self._actions()
        values = {'actions': actions, 'process':self.context}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result.update(resources)
        return result


DEFAULTMAPPING_ACTIONS_VIEWS.update({SeeProcessesDef:ProcessDefinitionContainerView,
                                     SeeProcesses:RuntimeView,
                                     StatisticProcessesDef:ProcessDefinitionStatisticView,
                                     SeeProcessDef:ProcessDefinitionView,
                                     InstanceProcessesDef:ProcessesPDDefinitionView,
                                     StatisticProcesses: ProcessStatisticView,
                                     SeeProcess:ProcessView,
                                     StatisticProcess:StatisticProcessView,
                                     SeeProcessDatas:ProcessDataView,
                                     DoActivitiesProcess:DoActivitiesProcessView})
