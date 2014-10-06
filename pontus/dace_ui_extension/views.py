# -*- coding: utf8 -*-
import colander
from pyramid.threadlocal import get_current_registry
from pyramid.view import view_config

from dace.objectofcollaboration.runtime import Runtime
from dace.objectofcollaboration.services.processdef_container import ProcessDefinitionContainer
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
from pontus.view import BasicView, ViewError, merge_dicts
from pontus.form import FormView
from pontus.schema import Schema
from pontus.widget import Select2Widget
from pontus.dace_ui_extension.interfaces import IDaceUIAPI
from pontus.dace_ui_extension import calculatePage
from pontus.view_operation import MultipleView


@view_config(
    name='Processes',
    context=Runtime,
    renderer='pontus:templates/view.pt'
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
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,'dace_ui_api')
        result = dace_ui_api.update_processes(self, self.context.processes, self.__class__.__name__+'AllProcesses')
        return result


@view_config(
    name='StatisticRun',
    context=Runtime,
    renderer='pontus:templates/view.pt'
    )
class ProcessStatisticView(BasicView):

    title = 'Tableau de bord'
    item_template = 'pontus:templates/subview_sample.pt'
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
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,'dace_ui_api')
        values = dace_ui_api.statistic_processes(self, self.context.processes, self.__class__.__name__)
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
    renderer='pontus:templates/view.pt'
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
        for p in processes:
            nav_bar = NavBarPanel(p, self.request)
            actions = nav_bar()
            processe = {'url':self.request.resource_url(p, '@@index'), 'process':p, 'nav_bar':actions}
            if p.discriminator in allprocesses:
                allprocesses[p.discriminator].append(processe)
            else:
                allprocesses[p.discriminator] = [processe]

        return allprocesses

    def update(self):
        self.execute(None)
        result = {}
        allprocessesdef = [{'title':k, 'processes':v} for k, v in self._processes().items()]
        values = {'allprocessesdef': allprocessesdef}
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result  = merge_dicts(self.requirements_copy, result)
        return result


@view_config(
    name='StatisticDef',
    context=ProcessDefinition,
    renderer='pontus:templates/view.pt'
    )
class ProcessDefinitionStatisticView(BasicView):

    title = 'Tableau de bord'
    item_template = 'pontus:templates/subview_sample.pt'
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
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,'dace_ui_api')
        values = dace_ui_api.statistic_processes(self, self.context.started_processes, self.__class__.__name__)
        dates = dace_ui_api.statistic_dates(self, self.context.started_processes)
        values['dates'] = dates
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result  = merge_dicts(self.requirements_copy, result)
        return result


@view_config(
    name='ProcessDef',
    context=ProcessDefinition,
    renderer='pontus:templates/view.pt'
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
    renderer='pontus:templates/view.pt'
    )
class ProcessesPDDefinitionView(BasicView):

    title = 'Les instance de la definition'
    template = 'pontus:dace_ui_extension/templates/processinstances_view.pt'
    name = 'ProcessInst'
    behaviors = [InstanceProcessesDef]
    requirements = {'css_links':[],
                    'js_links':['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']}

    def _processes(self, tabid):
        processes = sorted(self.context.started_processes, key=lambda p: p.created_at)
        page, pages, processes = calculatePage(processes, self, tabid)
        allprocesses = []
        for p in processes:
            processe = {'url':self.request.resource_url(p, '@@index'), 'process':p}
            allprocesses.append(processe)

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
                  'url': self.request.resource_url(self.context, '@@ProcessInst')}
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result  = merge_dicts(self.requirements_copy, result)
        return result


@view_config(
    name='Process',
    context=Process,
    renderer='pontus:templates/view.pt'
    )
class ProcessView(BasicView):

    title = 'Les detail du processus'
    template = 'pontus:dace_ui_extension/templates/process_view.pt'
    name ='Process'
    behaviors = [SeeProcess]

    def _actions(self):
        definition = self.context.definition
        definition_actions = sorted(definition.actions, key=lambda a: a.title) #les action du group Voir @TODO !
        alldefinitions_actions = []
        resources = {}
        resources['js_links'] = []
        resources['css_links'] = []
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,'dace_ui_api')
        for a in definition_actions:
            view = DEFAULTMAPPING_ACTIONS_VIEWS[a.action._class_]
            view_instance = view(definition, self.request)
            view_result = view_instance.get_view_requirements()
            body = ''
            if 'coordinates' in view_result:
                body = view_result['coordinates'][view_instance .coordinates][0]['body']

            action_infos = dace_ui_api.action_infomrations(action=a.action, context=definition, request=self.request)
            action_infos.update({'body':body, 'actionurl': a.url})
            alldefinitions_actions.append(action_infos)
            if 'js_links' in view_result:
                resources['js_links'].extend(view_result['js_links'])

            if 'css_links' in view_result:
                resources['css_links'].extend(view_result['css_links'])

        return resources, alldefinitions_actions

    def update(self):
        self.execute(None)
        result = {}
        resources, actions = self._actions()
        values = {'actions': actions, 'definition':self.context.definition ,'defurl':self.request.resource_url(self.context.definition, '@@index')}
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result.update(resources)
        return result


@view_config(
    name = 'Statistic',
    context=Process,
    renderer='pontus:templates/view.pt'
    )
class StatisticProcessView(BasicView):

    title = 'Tableau de bord'
    item_template = 'pontus:templates/subview_sample.pt'
    template = 'pontus:dace_ui_extension/templates/processstatistic_view.pt'
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
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


@view_config(
    name = 'lesdonneesmanipulees',
    context=Process,
    renderer='pontus:templates/view.pt'
    )
class ProcessDataView(BasicView):

    title = 'Les donnees manipulees'
    template = 'pontus:dace_ui_extension/templates/processdatas_view.pt'
    name='lesdonneesmanipulees'
    behaviors = [SeeProcessDatas]
    requirements = {'css_links':[],
                    'js_links':['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']}

    def _datas(self, involveds):
        alldatas = []
        for pname, inv in involveds.items():
            name = pname
            for i, d in enumerate(inv[1]):
                iscurrent = inv[4]
                index = inv[3]
                name = inv[2]
                if index == -1:
                    index = i+1

                if iscurrent is None:
                    if i == (len(inv[1]) - 1):
                        iscurrent = True

                alldatas.append({'url':self.request.resource_url(d, '@@index'),
                                 'data':d,
                                 'iscreator': inv[5] == 'created',
                                 'iscollection': inv[0] == 'collection',
                                 'relationname': name,
                                 'index': index,
                                 'iscurrent': iscurrent})

        return alldatas


    def update(self):
        self.execute(None)
        result = {}
        all_involveds = self._datas(self.context.execution_context.all_classified_involveds())
        involveds = [a for a in all_involveds if a['iscurrent']]
        values = {'datas': involveds, 'alldatas':all_involveds , 'tabid':self.__class__.__name__+'AllDatas'}
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result  = merge_dicts(self.requirements_copy, result)
        return result




@view_config(
    name = 'actionsrealiser',
    context=Process,
    renderer='pontus:templates/view.pt'
    )
class DoActivitiesProcessView(BasicView):

    title = 'Les actions a realiser'
    template = 'pontus:dace_ui_extension/templates/processactions_view.pt'
    name='actionsrealiser'
    behaviors = [DoActivitiesProcess]
    requirements = {'css_links':[],
                    'js_links':['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']}

    def _modal_views(self, all_actions, form_id, caa=False):
        action_updated=False
        resources = {}
        resources['js_links'] = []
        resources['css_links'] = []
        allbodies_actions = []
        updated_view = None
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,'dace_ui_api')
        for t in all_actions:
            a = t[1]
            c = t[0]
            view = DEFAULTMAPPING_ACTIONS_VIEWS[a.action._class_]
            view_instance = view(c, self.request, behaviors=[a.action])
            view_result = {}
            if not action_updated and form_id is not None and form_id.startswith(view_instance.viewid):
                action_updated = True
                updated_view = view_instance
                view_result = view_instance()
            else:
                view_result = view_instance.get_view_requirements()

            if updated_view is view_instance and  view_instance.isexecutable and view_instance.finished_successfully:
                return True, True, None, None

            if isinstance(view_result, dict):
                action_infos = {}
                if updated_view is view_instance and (not view_instance.isexecutable or (view_instance.isexecutable and not view_instance.finished_successfully)) :
                    action_infos['toreplay'] = True
                    if not view_instance.isexecutable:
                        action_infos['finished'] = True

                if caa:
                    actions_as = sorted(a.action.actions, key=lambda aa: aa.action.behavior_id)
                    a_actions = [(a.action, aa) for aa in actions_as]
                    toreplay, action_updated_as, resources_as, allbodies_actions_as = self._modal_views(a_actions, form_id)
                    if toreplay:
                        return True, True, None, None

                    if action_updated_as:
                        action_updated = True

                    resources['js_links'].extend(resources_as['js_links'])
                    resources['js_links'] = list(set(resources['js_links']))
                    resources['css_links'].extend(resources_as['css_links'])
                    resources['css_links'] =list(set(resources['css_links']))
                    action_infos['actions'] = allbodies_actions_as

                body = ''
                if 'coordinates' in view_result:
                    body = view_instance.render_item(view_result['coordinates'][view_instance.coordinates][0], view_instance.coordinates, None)
                assigned_to = sorted(a.action.assigned_to, key=lambda u: u.__name__)
                users= []
                for user in assigned_to:
                    users.append({'title':user.__name__, 'userurl': self.request.resource_url(user, '@@contents')})

                action_infos.update(dace_ui_api.action_infomrations(action=a.action, context=c, request=self.request))
                action_infos.update({'body':body,
                             'ismultiinstance':hasattr(a.action,'principalaction'),
                             'actionurl': a.url,
                             'data': c,
                             'dataurl': self.request.resource_url(c, '@@index'),
                             'assignedto': users})
                allbodies_actions.append(action_infos)
                if 'js_links' in view_result:
                    resources['js_links'].extend(view_result['js_links'])
                    resources['js_links'] = list(set(resources['js_links']))

                if 'css_links' in view_result:
                    resources['css_links'].extend(view_result['css_links'])
                    resources['css_links'] =list(set(resources['css_links']))

                if 'finished' in action_infos:
                    view_resources= {}
                    view_resources['js_links'] = []
                    view_resources['css_links'] = []
                    if 'js_links' in view_result:
                        view_resources['js_links'].extend(view_result['js_links'])

                    if 'css_links' in view_result:
                        view_resources['css_links'].extend(view_result['css_links'])

                    return True, True, view_resources, [action_infos]


        return False, action_updated, resources, allbodies_actions

    def _actions(self):
        involveds = self.context.execution_context.all_active_involveds().values()
        datas = []
        for inv in involveds:
            if not(inv[1] in datas):
                datas.extend(inv[1])

        datas = list(set(datas))
        datas = sorted(datas, key=lambda d: d.title)
        all_actions = []
        messages = {}
        for d in datas:
            actions = [a for a in d.actions if a.action.process is self.context]
            actions = sorted(actions, key=lambda a: a.action.__name__)
            p_actions = [(d,a) for a in actions]
            all_actions.extend(p_actions)

        form_id = None
        if '__formid__' in self.request.POST:
            form_id = self.request.POST['__formid__']

        toreplay, action_updated, resources, allbodies_actions = self._modal_views(all_actions, form_id, True)
        if toreplay:
            self.request.POST.clear()
            old_resources = resources
            old_allbodies_actions = allbodies_actions
            action_updated, messages, resources, allbodies_actions = self._actions()
            if old_resources is not None:
                if 'js_links' in old_resources:
                    resources['js_links'].extend(old_resources['js_links'])
                    resources['js_links'] = list(set(resources['js_links']))

                if 'css_links' in old_resources:
                    resources['css_links'].extend(old_resources['css_links'])
                    resources['css_links'] =list(set(resources['css_links']))

            if old_allbodies_actions is not None:
                allbodies_actions.extend(old_allbodies_actions)

            return True , messages, resources, allbodies_actions

        if form_id is not None and not action_updated:
            error = ViewError()
            error.principalmessage = u"Action non realisee"
            error.causes = ["Vous n'avez plus le droit de realiser cette action.", "L'action est verrouillee par un autre utilisateur."]
            message = self._get_message(error)
            messages.update({error.type: [message]})

        return action_updated, messages, resources, allbodies_actions

    def update(self):
        self.execute(None)
        result = {}
        action_updated, messages, resources, actions = self._actions()
        values = {'actions': actions,
                  'process':self.context,
                  'defurl':self.request.resource_url(self.context.definition, '@@index'),
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
    context = node.bindings['context']
    request = node.bindings['request']
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
    renderer='pontus:templates/view.pt',
    )
class AssignToUsersView(FormView):

    title = 'Assigner l\'activitee'
    schema = AssignToUsersViewSchema()
    formid = 'assign_activity_form'
    behaviors = [AssignToUsers]
    name ='assign_activity'


class AssignedUsersView(BasicView):
    title = 'Les utilisateurs assignies'
    name='assigned_users'
    template = 'pontus.dace_ui_extension:templates/assigned_users.pt'

    def update(self):
        assigned_to = sorted(self.context.assigned_to, key=lambda u: u.__name__)
        users= []
        for user in assigned_to:
            users.append({'title':user.__name__, 'userurl': self.request.resource_url(user, '@@contents')})

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
    name ='assign_action_form'
    formid = 'assigne_action_form'
    schema = AssignToUsersViewSchema()
    behaviors = [AssignActionToUsers]
    validate_behaviors = False


@view_config(
    name='assign_action',
    context=IBusinessAction,
    renderer='pontus:templates/view.pt',
    )
class AssignActionToUsersMultipleView(MultipleView):
    title = 'Assigner l\'action'
    name = 'assign_action'
    template = 'pontus.dace_ui_extension:templates/sample_mergedmultipleview.pt'
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
