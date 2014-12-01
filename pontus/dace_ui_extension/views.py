# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi
# -*- coding: utf8 -*-
import colander
from pyramid.threadlocal import get_current_registry
from pyramid.view import view_config

from dace.objectofcollaboration.runtime import Runtime
from dace.objectofcollaboration.services.processdef_container import (
    ProcessDefinitionContainer)
from dace.processdefinition.processdef import ProcessDefinition
from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from dace.processinstance.process import Process
from dace.util import getSite
from dace.interfaces import (
    IActivity,
    IBusinessAction)

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
           DoActivitiesProcess,
           AssignToUsers,
           AssignActionToUsers)
from pontus.view import BasicView
from pontus.util import merge_dicts
from pontus.form import FormView
from pontus.schema import Schema
from pontus.widget import Select2Widget
from pontus.dace_ui_extension.interfaces import IDaceUIAPI
from pontus.dace_ui_extension import calculatePage
from pontus.view_operation import MultipleView


@view_config(
    name='Processes',
    context=Runtime,
    renderer='pontus:templates/views_templates/grid.pt'
    )
class RuntimeView(BasicView):

    title = 'Processes'
    template = 'pontus:dace_ui_extension/templates/runtime_view.pt'
    name = 'Processes'
    behaviors = [SeeProcesses]
    requirements = {'css_links':[],
                    'js_links':['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']}

    def update(self):
        self.execute(None)
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,
                                                        'dace_ui_api')
        result = dace_ui_api.update_processes(self, self.context.processes, 
                                      self.__class__.__name__+'AllProcesses')
        return result


@view_config(
    name='StatisticRun',
    context=Runtime,
    renderer='pontus:templates/views_templates/grid.pt'
    )
class ProcessStatisticView(BasicView):

    title = 'Tableau de bord'
    wrapper_template = 'pontus:dace_ui_extension/templates/simple_view_wrapper.pt'
    template = 'pontus:dace_ui_extension/templates/runtimeprocesses_statistic_view.pt'
    name = 'StatisticRun'
    coordinates = 'left'
    behaviors = [StatisticProcesses]
    requirements = {'css_links':[],
                    'js_links':['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js',
                                 'pontus.dace_ui_extension:static/dygraph/dygraph-combined.js' ]}

    def update(self):
        self.execute(None)
        result = {}
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,
                                                        'dace_ui_api')
        values = dace_ui_api.statistic_processes(self, self.context.processes, 
                                                 self.__class__.__name__)
        dates = dace_ui_api.statistic_dates(self, self.context.processes)
        values['dates'] = dates
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result  = merge_dicts(self.requirements_copy, result)
        return result


@view_config(
    name='ProcessesDef',
    context=ProcessDefinitionContainer,
    renderer='pontus:templates/views_templates/grid.pt'
    )
class ProcessDefinitionContainerView(BasicView):

    title = 'Processes'
    template = 'pontus:dace_ui_extension/templates/defcontainer_view.pt'
    name = 'ProcessesDef'
    behaviors = [SeeProcessesDef]
    requirements = {'css_links':[],
                    'js_links':['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']}

    def _processes(self):
        from pontus.panels import NavBarPanel
        processes = sorted(self.context.definitions, key=lambda p: p.__name__)
        allprocesses = {}
        for process in processes:
            nav_bar = NavBarPanel(process, self.request)
            actions = nav_bar()
            process_data = {
                        'url':self.request.resource_url(process, '@@index'), 
                        'process':process, 
                        'nav_bar':actions}
            if process.discriminator in allprocesses:
                allprocesses[process.discriminator].append(process_data)
            else:
                allprocesses[process.discriminator] = [process_data]

        return allprocesses

    def update(self):
        self.execute(None)
        result = {}
        allprocessesdef = [{'title':k, 'processes':v} \
                           for k, v in self._processes().items()]
        values = {'allprocessesdef': allprocessesdef}
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result  = merge_dicts(self.requirements_copy, result)
        return result


@view_config(
    name='StatisticDef',
    context=ProcessDefinition,
    renderer='pontus:templates/views_templates/grid.pt'
    )
class ProcessDefinitionStatisticView(BasicView):

    title = 'Tableau de bord'
    wrapper_template = 'pontus:dace_ui_extension/templates/simple_view_wrapper.pt'
    template = 'pontus:dace_ui_extension/templates/processdef_statistic_view.pt'
    name = 'StatisticDef'
    coordinates = 'left'
    behaviors = [StatisticProcessesDef]
    requirements = {'css_links':[],
                    'js_links':['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js',
                                 'pontus.dace_ui_extension:static/dygraph/dygraph-combined.js' ]}

    def update(self):
        self.execute(None)
        result = {}
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,
                                                        'dace_ui_api')
        values = dace_ui_api.statistic_processes(self, 
                                                 self.context.started_processes,
                                                 self.__class__.__name__)
        dates = dace_ui_api.statistic_dates(self, 
                    self.context.started_processes)
        values['dates'] = dates
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result  = merge_dicts(self.requirements_copy, result)
        return result


@view_config(
    name='ProcessDef',
    context=ProcessDefinition,
    renderer='pontus:templates/views_templates/grid.pt'
    )
class ProcessDefinitionView(BasicView):

    title = 'La definition du processus'
    template = 'pontus:dace_ui_extension/templates/processdef_view.pt'
    name = 'ProcessDef'
    behaviors = [SeeProcessDef]

    def update(self):
        self.execute(None)
        result = {}
        values = {'processdef': self.context}
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


@view_config(
    name='ProcessInst',
    context=ProcessDefinition,
    renderer='pontus:templates/views_templates/grid.pt'
    )
class ProcessesPDDefinitionView(BasicView):

    title = 'Les instance de la definition'
    template = 'pontus:dace_ui_extension/templates/processinstances_view.pt'
    name = 'ProcessInst'
    behaviors = [InstanceProcessesDef]
    requirements = {'css_links':[],
                    'js_links':['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']}

    def _processes(self, tabid):
        processes = sorted(self.context.started_processes, 
                           key=lambda p: p.created_at)
        page, pages, processes = calculatePage(processes, self, tabid)
        allprocesses = []
        for process in processes:
            process_data = {
                        'url':self.request.resource_url(process, '@@index'), 
                        'process':process}
            allprocesses.append(process_data)

        return page, pages, allprocesses

    def update(self):
        self.execute(None)
        result = {}
        tabid = self.__class__.__name__+'AllProcesses'
        page, pages, allprocesses = self._processes(tabid)
        values = {'processes': allprocesses,
                  'p_id': self.context.title,
                  'tabid':tabid,
                  'page': page,
                  'pages': pages,
                  'url': self.request.resource_url(self.context, 
                                                   '@@ProcessInst')}
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result  = merge_dicts(self.requirements_copy, result)
        return result


@view_config(
    name='Process',
    context=Process,
    renderer='pontus:templates/views_templates/grid.pt'
    )
class ProcessView(BasicView):

    title = 'Les detail du processus'
    template = 'pontus:dace_ui_extension/templates/process_view.pt'
    name = 'Process'
    behaviors = [SeeProcess]


    def update(self):
        self.execute(None)
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,
                                                        'dace_ui_api')
        all_actions = dace_ui_api.get_actions(
                                     [self.context.definition], self.request)
        action_updated, messages, \
        resources, actions = dace_ui_api.update_actions(
                                          self.request, all_actions,
                                          False, True)
        result = {}
        values = {'actions': actions, 
                  'definition':self.context.definition}
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        item['messages'] = messages
        item['isactive'] = action_updated
        result['coordinates'] = {self.coordinates:[item]}
        result.update(resources)
        return result


@view_config(
    name = 'Statistic',
    context=Process,
    renderer='pontus:templates/views_templates/grid.pt'
    )
class StatisticProcessView(BasicView):

    title = 'Tableau de bord'
    wrapper_template = 'pontus:dace_ui_extension/templates/simple_view_wrapper.pt'
    template = 'pontus:dace_ui_extension/templates/processstatistic_view.pt'
    name = 'Statistic'
    coordinates = 'left'
    behaviors = [StatisticProcess]

    def update(self):
        self.execute(None)
        result = {}
        values = {}
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


@view_config(
    name = 'lesdonneesmanipulees',
    context=Process,
    renderer='pontus:templates/views_templates/grid.pt'
    )
class ProcessDataView(BasicView):

    title = 'Les donnees manipulees'
    template = 'pontus:dace_ui_extension/templates/processdatas_view.pt'
    name = 'lesdonneesmanipulees'
    behaviors = [SeeProcessDatas]
    requirements = {'css_links':[],
                    'js_links':['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']}

    def _datas(self, involveds):
        alldatas = []
        for pname, inv in involveds.items():
            name = pname
            for i, entity in enumerate(inv['entities']):
                iscurrent = inv['is_current']
                index = inv['index']
                name = inv['name']
                if index == -1:
                    index = i+1

                if iscurrent is None:
                    if i == (len(inv['entities']) - 1):
                        iscurrent = True

                alldatas.append({'url':self.request.resource_url(entity, 
                                                                 '@@index'),
                                 'data':entity,
                                 'iscreator': inv['assocition_kind']=='created',
                                 'iscollection': inv['type']=='collection',
                                 'relationname': name,
                                 'index': index,
                                 'iscurrent': iscurrent})

        return alldatas


    def update(self):
        self.execute(None)
        result = {}
        all_involveds = self._datas(
                   self.context.execution_context.all_classified_involveds())
        involveds = [a for a in all_involveds if a['iscurrent']]
        values = {'datas': involveds, 
                  'alldatas':all_involveds, 
                  'tabid':self.__class__.__name__+'AllDatas'}
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result  = merge_dicts(self.requirements_copy, result)
        return result




@view_config(
    name = 'actionsrealiser',
    context=Process,
    renderer='pontus:templates/views_templates/grid.pt'
    )
class DoActivitiesProcessView(BasicView):

    title = 'Les actions a realiser'
    template = 'pontus:dace_ui_extension/templates/processactions_view.pt'
    name = 'actionsrealiser'
    behaviors = [DoActivitiesProcess]
    requirements = {'css_links':[],
                    'js_links':['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']}

    def update(self):
        self.execute(None)
        involveds = self.context.execution_context.all_active_involveds().values()
        involveds = [e['entities'] for e in involveds]
        involveds = [entity for entities in involveds for entity in entities]
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,
                                                        'dace_ui_api')
        all_actions = dace_ui_api.get_actions(
                                     involveds, self.request, self.context)
        action_updated, messages, \
        resources, actions = dace_ui_api.update_actions(
                                          self.request, all_actions,
                                          False, False)
        result = {}
        values = {'actions': actions,
                  'process':self.context,
                  'tabid':self.__class__.__name__+'AllActions'}
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        item['messages'] = messages
        item['isactive'] = action_updated
        result['coordinates'] = {self.coordinates:[item]}
        result.update(resources)
        result  = merge_dicts(self.requirements_copy, result)
        return result


@colander.deferred
def defaultusers(node, kw):
    context = node.bindings['context']
    return  context.assigned_to

@colander.deferred
def listchoice(node, kw):
    values = []
    prop = getSite()['principals']['users'].values()
    values = [(i, i.__name__) for i in prop]
    return Select2Widget(values=values, multiple=True)


class AssignToUsersViewSchema(Schema):

        users = colander.SchemaNode(
                colander.Set(),
                widget=listchoice,
                default=defaultusers,
                title='Les utilisateurs',
                required=False
                )


@view_config(
    name='assign_activity',
    context=IActivity,
    renderer='pontus:templates/views_templates/grid.pt',
    )
class AssignToUsersView(FormView):

    title = 'Assigner l\'activitee'
    schema = AssignToUsersViewSchema()
    formid = 'assign_activity_form'
    behaviors = [AssignToUsers]
    name = 'assign_activity'


class AssignedUsersView(BasicView):
    title = 'Les utilisateurs assignies'
    name = 'assigned_users'
    template = 'pontus.dace_ui_extension:templates/assigned_users.pt'

    def update(self):
        assigned_to = sorted(self.context.assigned_to, 
                             key=lambda u: u.__name__)
        users = []
        for user in assigned_to:
            users.append({'title':user.__name__, 
                          'userurl': self.request.resource_url(user, 
                                                       '@@contents')})

        result = {}
        values = {
                'users': users,
               }
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


class AssignActionToUsersView(FormView):

    title = 'Assigner l\'action'
    name = 'assign_action_form'
    formid = 'assigne_action_form'
    schema = AssignToUsersViewSchema()
    behaviors = [AssignActionToUsers]
    validate_behaviors = False


@view_config(
    name='assign_action',
    context=IBusinessAction,
    renderer='pontus:templates/views_templates/grid.pt',
    )
class AssignActionToUsersMultipleView(MultipleView):
    title = 'Assigner l\'action'
    name = 'assign_action'
    template = 'pontus.dace_ui_extension:templates/simple_mergedmultipleview.pt'
    views = (AssignedUsersView, AssignActionToUsersView)
    validators = [AssignActionToUsers.get_validator()]


#un decorateur c'est mieux!
DEFAULTMAPPING_ACTIONS_VIEWS.update({SeeProcessesDef:ProcessDefinitionContainerView,
                                     SeeProcesses:RuntimeView,
                                     StatisticProcessesDef:ProcessDefinitionStatisticView,
                                     SeeProcessDef:ProcessDefinitionView,
                                     InstanceProcessesDef:ProcessesPDDefinitionView,
                                     StatisticProcesses: ProcessStatisticView,
                                     SeeProcess:ProcessView,
                                     StatisticProcess:StatisticProcessView,
                                     SeeProcessDatas:ProcessDataView,
                                     DoActivitiesProcess:DoActivitiesProcessView,
                                     AssignToUsers:AssignToUsersView,
                                     AssignActionToUsers:AssignActionToUsersMultipleView})
