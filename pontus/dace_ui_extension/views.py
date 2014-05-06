# -*- coding: utf8 -*-
import re
import colander
import datetime
from pyramid.response import Response

from substanced.sdi import mgmt_view
from substanced.sdi import LEFT
from substanced.util import get_oid

from dace.objectofcollaboration.runtime import Runtime
from dace.objectofcollaboration.services.processdef_container import ProcessDefinitionContainer
from dace.processdefinition.processdef import ProcessDefinition
from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from dace.processinstance.process import Process
from dace.util import getSite, get_obj
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
from pontus.view import BasicView, ViewError
from pontus.form import FormView
from pontus.schema import Schema
from pontus.widget import  SequenceWidget, Select2Widget


def calculatePage(elements, view, tabid):
    page = view.params('page'+tabid)
    number = view.params('number'+tabid)
    if number is None:
        number = 7
    else:
        number = int(number)

    import numpy as np
    pages = int(np.ceil(float(len(elements))/number))
    if pages > 0:
        if page is None:
            page = 1
        else:
            page = int(page)

        endpage = page*number
        if (endpage) > len(elements):
            endpage = len(elements)

        elements = elements[((page-1)*number):endpage]

    return page, pages, elements


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
        allprocesses = []
        nb_encours = 0
        nb_bloque = 0
        nb_termine = 0
        for p in processes:
            bloced = not p.getWorkItems()
            processe = {'url':self.request.mgmt_path(p, '@@index'), 'process':p, 'bloced':bloced, 'created_at': p.created_at}
            allprocesses.append(processe)
            if p._finished:
                nb_termine += 1
            elif bloced:
                nb_bloque += 1
            else:
                nb_encours += 1

        return nb_encours, nb_bloque, nb_termine, allprocesses

    def _update(self, processes, tabid):
        result = {}
        processes = sorted(processes, key=lambda p: p.created_at)
        page, pages, processes = calculatePage(processes, self, tabid)
        nb_encours, nb_bloque, nb_termine, allprocesses = self._processes(processes)
        #import pdb; pdb.set_trace()
        values = {'processes': allprocesses, 
                  'encours':nb_encours,
                  'bloque':nb_bloque,
                  'termine':nb_termine,
                  'tabid':tabid,
                  'page': page,
                  'pages': pages,
                  'url': self.request.relative_url(None)}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result['js_links']=['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']
        return result

    def update(self):
        self.execute(None)
        result = self._update(self.context.processes, self.__class__.__name__+'AllProcesses')
        return result


@mgmt_view(
    name = 'StatisticRun',
    context=Runtime,
    renderer='pontus:templates/view.pt'
    )
class ProcessStatisticView(BasicView):

    title = 'Tableau de bord'
    item_template = 'pontus:templates/subview_sample.pt'
    self_template = 'pontus:dace_ui_extension/templates/runtimeprocesses_statistic_view.pt'
    viewid = 'statistic'
    name='StatisticRun'
    coordinates = 'left'
    behaviors = [StatisticProcesses]

    def _dates(self, processes):
        dates = {}
        for p in processes:
            created_at = p.created_at
            date = str(datetime.datetime(created_at.year, created_at.month, created_at.day, created_at.hour, created_at.minute))
            if date in dates:
                dates[date] += 1
            else:
                dates[date] = 1

        dates = sorted(dates.iteritems(), key=lambda i: i[0])
        return dates

    def _values(self, processes, tabid):
        runtime_view = RuntimeView(self.context, self.request)
        nb_encours, nb_bloque, nb_termine, allprocesses =  runtime_view._processes(processes)
        
        blocedprocesses = [p['process'] for p in  allprocesses if p['bloced'] and not p['process']._finished ]
        terminetedprocesses = [ p['process'] for p in  allprocesses if p['process']._finished]
        activeprocesses = [ p['process'] for p in  allprocesses if  not p['process']._finished and not p['bloced']]

        result_bloced_runtime_v = runtime_view._update(blocedprocesses, tabid+'BlocedProcesses')
        item = result_bloced_runtime_v['coordinates'][runtime_view.coordinates][0]
        bloquesBody =item['body']

        result_encours_runtime_v = runtime_view._update(activeprocesses, tabid+'RunProcesses')
        item = result_encours_runtime_v['coordinates'][runtime_view.coordinates][0]
        encoursBody =item['body']

        result_termines_runtime_v = runtime_view._update(terminetedprocesses, tabid+'TerminetedProcesses')
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
        values = self._values(self.context.processes, self.__class__.__name__)
        dates = self._dates(self.context.processes)
        values['dates'] = dates
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result['js_links']=['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js',
                            'pontus.dace_ui_extension:static/dygraph/dygraph-combined.js']

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
        processes = sorted(self.context.definitions, key=lambda p: p.__name__)
        allprocesses = {}
        for p in processes:
            nav_bar = NavBarPanel(p, self.request)
            actions = nav_bar()
            processe = {'url':self.request.mgmt_path(p, '@@index'), 'process':p, 'nav_bar':actions}
            if p.discriminator in allprocesses:
                allprocesses[p.discriminator].append(processe)
            else:  
                allprocesses[p.discriminator] = [processe]

        return allprocesses

    def update(self):
        self.execute(None)
        result = {}
        allprocessesdef = [{'title':k, 'processes':v} for k, v in self._processes().iteritems()]
        values = {'allprocessesdef': allprocessesdef}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result['js_links']=['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']
        return result


@mgmt_view(
    name = 'StatisticDef',
    context=ProcessDefinition,
    renderer='pontus:templates/view.pt'
    )
class ProcessDefinitionStatisticView(BasicView):

    title = 'Tableau de bord'
    item_template = 'pontus:templates/subview_sample.pt'
    self_template = 'pontus:dace_ui_extension/templates/processdef_statistic_view.pt'
    viewid = 'statistic'
    name='StatisticDef'
    coordinates = 'left'
    behaviors = [StatisticProcessesDef]

    def update(self):
        self.execute(None)
        result = {}
        processStatisticView_instance = ProcessStatisticView(self.context, self.request)
        values = processStatisticView_instance._values(self.context.started_processes, self.__class__.__name__)
        dates = processStatisticView_instance._dates(self.context.started_processes)
        values['dates'] = dates
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result['js_links']=['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js',
                            'pontus.dace_ui_extension:static/dygraph/dygraph-combined.js']
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

    def _processes(self, tabid):
        processes = sorted(self.context.started_processes, key=lambda p: p.created_at)
        page, pages, processes = calculatePage(processes, self, tabid)
        allprocesses = []
        for p in processes:
            processe = {'url':self.request.mgmt_path(p, '@@index'), 'process':p}
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
                  'url': self.request.relative_url(None)}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result['js_links']=['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']
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
        definition_actions = sorted(definition.actions, key=lambda a: a.title) #les action du group Voir @TODO !
        alldefinitions_actions = []
        resources = {}
        resources['js_links'] = []
        resources['css_links'] = []
        for a in definition_actions:
           view = DEFAULTMAPPING_ACTIONS_VIEWS[a.action._class]
           view_instance = view(definition, self.request) 
           view_result = view_instance.update()
           body = view_result['coordinates'][view.coordinates][0]['body']
           alldefinitions_actions.append({'body':body, 'action':a.action})
           if 'js_links' in view_result:
               resources['js_links'].extend(view_result['js_links'])

           if 'css_links' in view_result:
               resources['css_links'].extend(view_result['css_links'])

        return resources, alldefinitions_actions

    def update(self):
        self.execute(None)
        result = {}
        resources, actions = self._actions()
        values = {'actions': actions, 'definition':self.context.definition ,'defurl':self.request.mgmt_path(self.context.definition, '@@index')}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result.update(resources)
        return result


@mgmt_view(
    name = 'Statistic',
    context=Process,
    renderer='pontus:templates/view.pt'
    )
class StatisticProcessView(BasicView):

    title = 'Tableau de bord'
    item_template = 'pontus:templates/subview_sample.pt'
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

    def _datas(self, involveds):
        alldatas = []
        for pname, inv in involveds.iteritems():
            name = pname
            for i, d in enumerate(inv[1]):
                iscollection =  (inv[0] == 'collection')
                iscurrent = inv[4]
                index = inv[3]
                name = inv[2]
                if index == -1:
                    index = i+1
       
                if iscurrent is None:
                    if i == (len(inv[1]) - 1):
                        iscurrent = True
                    
                alldatas.append({'url':self.request.mgmt_path(d, '@@index'),
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
        involveds = [a for a in all_involveds if a['iscurrent']] #self._datas(self.context.execution_context.all_active_involveds())
        
        values = {'datas': involveds, 'alldatas':all_involveds , 'tabid':self.__class__.__name__+'AllDatas'}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        result['js_links']=['pontus.dace_ui_extension:static/tablesorter-master/js/jquery.tablesorter.min.js']
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

    def _modal_views(self, all_actions, form_id, caa=False):
        action_updated=False
        resources = {}
        resources['js_links'] = []
        resources['css_links'] = []
        allbodies_actions = []
        updated_view = None
        for t in all_actions:
           a = t[1]
           c = t[0]
           view = DEFAULTMAPPING_ACTIONS_VIEWS[a.action._class]
           view_instance = view(c, self.request, behaviors=[a.action])
           if not action_updated and form_id is not None and form_id.startswith(view_instance.viewid):
               action_updated = True
               updated_view = view_instance

           view_result = {}
           view_result = view_instance.update()
           if updated_view is view_instance and view_instance.finished_successfully:
               return True, True, None, None
              
           if isinstance(view_result, dict):
               _item = {}
               if updated_view is view_instance and not view_instance.finished_successfully:
                   _item['toreplay'] = True

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
                   _item['actions'] = allbodies_actions_as

               body = view_result['coordinates'][view.coordinates][0]['body']
               action_id = a.action.behavior_id
               try:
                   action_id = action_id+str(get_oid(a.action))+'_'+str(get_oid(c))
               except Exception:
                   try:
                       action_id = action_id+'Start'+'_'+str(get_oid(c))
                   except Exception:
                       action_id = action_id+'Start'

               assigned_to = sorted(a.action.assigned_to, key=lambda u: u.__name__)
               users= []
               for user in assigned_to:
                   users.append({'title':user.__name__, 'userurl': self.request.mgmt_path(user, '@@contents')})

               _item.update({'body':body,
                             'action':a.action,
                             'ismultiinstance':hasattr(a.action,'principalaction'),
                             'action_id':action_id,
                             #'action_oid': get_oid(a.action),
                             'data': c,
                             'actionurl': a.url,
                             'dataurl': self.request.mgmt_path(c, '@@index'),
                             'assignedto': users})
               allbodies_actions.append(_item)
               if 'js_links' in view_result:
                   resources['js_links'].extend(view_result['js_links'])
                   resources['js_links'] = list(set(resources['js_links']))

               if 'css_links' in view_result:
                   resources['css_links'].extend(view_result['css_links'])
                   resources['css_links'] =list(set(resources['css_links']))

        return False, action_updated, resources, allbodies_actions

    def _actions(self):
        involveds = self.context.execution_context.all_active_involveds().values()
        datas = []
        for inv in involveds:
            if not(inv[1] in datas):
                datas.extend(inv[1])

        datas = list(set(datas))
        datas = sorted(datas, key=lambda d: d.__name__)
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
            action_updated, messages, resources, allbodies_actions = self._actions()
            return True , messages, resources, allbodies_actions

        if form_id is not None and not action_updated:
            error = ViewError()
            error.principalmessage = u"Action non realisee"
            error.causes = ["Vous n'avez plus le droit de realiser cette action.", "L'action est verrouillée par un autre utilisateur."]
            message = self._get_message(error)
            messages.update({error.type: [message]})

        return action_updated, messages, resources, allbodies_actions

    def update(self):
        self.execute(None)
        result = {}
        action_updated, messages, resources, actions = self._actions()
        values = {'actions': actions,
                  'process':self.context,
                  'defurl':self.request.mgmt_path(self.context.definition, '@@index'),
                  'tabid':self.__class__.__name__+'AllActions'}
        body = self.content(result=values, template=self.self_template)['body']
        item = self.adapt_item(body, self.viewid)
        item['messages'] = messages
        item['isactive'] = action_updated
        result['coordinates'] = {self.coordinates:[item]}
        result.update(resources)
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
                required=False
                )


@mgmt_view(
    name='assign_activity',
    context=IActivity,
    renderer='pontus:templates/view.pt',
    )
class AssignToUsersView(FormView):

    title = 'Assigner l\'activitee'
    schema = AssignToUsersViewSchema()
    formid = 'assign_activity_form'
    #coordinates = 'left'
    behaviors = [AssignToUsers]
    name='assign_activity'
    #use_ajax = True


@mgmt_view(
    name='assign_action',
    context=IBusinessAction,
    renderer='pontus:templates/view.pt',
    )
class AssignActionToUsersView(FormView):

    title = 'Assigner l\'action'
    schema = AssignToUsersViewSchema()
    formid = 'assigne_action_form'
    #coordinates = 'left'
    behaviors = [AssignActionToUsers]
    name='assign_action'
    #use_ajax = True


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
                                     AssignActionToUsers:AssignActionToUsersView})
