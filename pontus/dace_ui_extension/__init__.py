# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi
import datetime
from math import ceil
from zope.interface import implementer

from pyramid.threadlocal import get_current_request, get_current_registry
from pyramid.view import view_config
from pyramid import renderers

from substanced.util import get_oid

from dace.util import get_obj, find_service, utility, getAllBusinessAction
from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from dace.objectofcollaboration.entity import Entity

from pontus.view import BasicView, ViewError
from pontus.util import merge_dicts
from pontus.dace_ui_extension.interfaces import IDaceUIAPI

try:
    basestring
except NameError:
    basestring = str


def calculatePage(elements, view, tabid):
    page = view.params('page'+tabid)
    number = view.params('number'+tabid)
    if number is None:
        number = 7
    else:
        number = int(number)

    pages = int(ceil(float(len(elements))/number))
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


@utility(name='dace_ui_api')
@implementer(IDaceUIAPI)
class DaceUIAPI(object):

    def get_actions(self, 
                    contexts,
                    request,
                    process_or_id=None,
                    action_id=None, 
                    process_discriminator=None):
        all_actions = []
        process_id = None
        process = None
        if process_or_id and isinstance(process_or_id, basestring):
            process_id = process_or_id
        elif process_or_id:
            process = process_or_id

        for context in contexts:
            actions = getAllBusinessAction(context, request,
                         process_id=process_id, node_id=action_id,
                         process_discriminator=process_discriminator)
            if process:
                actions = [action for action in actions \
                           if action.process is process]

            actions = sorted(actions, key=lambda action: action.node_id)
            p_actions = [(context, a) for a in actions]
            all_actions.extend(p_actions)

        return all_actions

    def _modal_views(self, 
                     request, 
                     actions, 
                     form_id,
                     ignor_actionsofactions=True):
        action_updated = False
        resources = {}
        resources['js_links'] = []
        resources['css_links'] = []
        allbodies_actions = []
        updated_view = None
        for (context, action) in actions:
            #get view class
            view = DEFAULTMAPPING_ACTIONS_VIEWS[action._class_]
            #get view instance
            view_instance = view(context, request, 
                     behaviors=[action])
            view_result = {}
            #if the view instance is called then update the view
            if not action_updated and form_id and \
               view_instance.has_id(form_id):
                action_updated = True
                updated_view = view_instance
                view_result = view_instance()
            else:
                #else get view requirements
                view_result = view_instance.get_view_requirements()
            
            #if the view instance is executable and it is executable
            #and finished successfully return
            if updated_view is view_instance and \
               view_instance.isexecutable and \
               view_instance.finished_successfully:
                return True, True, None, None

            #if the view instance return a result
            if isinstance(view_result, dict):
                action_infos = {}
                #if the view instance is not executable or 
                #it is finished with an error
                if updated_view is view_instance and \
                   (not view_instance.isexecutable or \
                    (view_instance.isexecutable and \
                     not view_instance.finished_successfully)) :
                    action_infos['toreplay'] = True
                    if not view_instance.isexecutable:
                        action_infos['finished'] = True

                if not ignor_actionsofactions:
                    actions_as = sorted(action.actions, 
                        key=lambda call_action: call_action.action.behavior_id)
                    a_actions = [(action, call_action.action) \
                                 for call_action in actions_as]
                    toreplay, action_updated_as, \
                    resources_as, allbodies_actions_as = self._modal_views(
                                              request, a_actions, form_id)
                    if toreplay:
                        return True, True, None, None

                    if action_updated_as:
                        action_updated = True

                    resources['js_links'].extend(resources_as['js_links'])
                    resources['js_links'] = list(set(resources['js_links']))
                    resources['css_links'].extend(resources_as['css_links'])
                    resources['css_links'] = list(set(resources['css_links']))
                    action_infos['actions'] = allbodies_actions_as


                body = ''
                if 'coordinates' in view_result:
                    body = view_instance.render_item(
                     view_result['coordinates'][view_instance.coordinates][0], 
                     view_instance.coordinates, None)

                action_infos.update(
                        self.action_infomrations(action=action, 
                                                 context=context, 
                                                 request=request))
                action_infos.update({
                        'body':body,
                        'context': context,
                        'assigned_to': sorted(action.assigned_to, 
                                            key=lambda u: getattr(u, 'title', 
                                                                u.__name__))})
                allbodies_actions.append(action_infos)
                resources = merge_dicts(view_result, resources, 
                                        ('js_links', 'css_links'))
                resources['js_links'] = list(set(resources['js_links']))
                resources['css_links'] = list(set(resources['css_links']))

                if 'finished' in action_infos:
                    view_resources = {}
                    view_resources['js_links'] = []
                    view_resources['css_links'] = []
                    view_resources = merge_dicts(view_result, view_resources, 
                                        ('js_links', 'css_links'))

                    return True, True, view_resources, [action_infos]


        return False, action_updated, resources, allbodies_actions

    def update_actions(self, 
                 request,
                 all_actions,
                 ignor_form=False,
                 ignor_actionsofactions=True):
        messages = {}
        #find all business actions
        form_id = None
        #get submited form view
        if not ignor_form and '__formid__' in request.POST:
            #if request.POST['__formid__'].find(object_oid) >= 0:
            form_id = request.POST['__formid__']

        toreplay, action_updated, \
        resources, allbodies_actions = self._modal_views(
                                        request, all_actions,
                                        form_id, ignor_actionsofactions)
        if toreplay:
            request.POST.clear()
            old_resources = resources
            old_allbodies_actions = allbodies_actions
            action_updated, messages, \
            resources, allbodies_actions = self.update_actions(request, 
                                                         all_actions,
                                                         ignor_form)
            if old_resources is not None:
                resources = merge_dicts(old_resources, resources, 
                                        ('js_links', 'css_links'))
                resources['js_links'] = list(set(resources['js_links']))
                resources['css_links'] = list(set(resources['css_links']))

            if old_allbodies_actions is not None:
                allbodies_actions.extend(old_allbodies_actions)

            return True , messages, resources, allbodies_actions

        if form_id and \
           not action_updated and all_actions:
            error = ViewError()
            error.principalmessage = u"Action non realisee"
            error.causes = ["Vous n'avez plus le droit de realiser cette action.", 
                            "L'action est verrouillee par un autre utilisateur."]
            message = error.render_message(request)
            messages.update({error.type: [message]})

        return action_updated, messages, resources, allbodies_actions

    def action_infomrations(self, action, context, request=None, **args):
        action_id = action.behavior_id
        action_oid = 'start'
        context_oid = get_oid(context)
        try:
            action_oid = get_oid(action)
        except Exception:
            pass

        action_id= action_id+str(action_oid)+'_'+str(context_oid)
        after_url = self.afterexecution_viewurl(request=request, 
                                                action_uid=str(action_oid), 
                                                context_uid=str(context_oid))
        actionurl_update = self.updateaction_viewurl(request=request, 
                                                action_uid=str(action_oid), 
                                                context_uid=str(context_oid))
        if action_oid == 'start':
            after_url = self.afterexecution_viewurl(request=request,
                                                isstart=True,
                                                context_uid=str(context_oid),
                                                pd_id=action.node.process.id,
                                                action_id=action.node.__name__,
                                                behavior_id=action.behavior_id)
            actionurl_update = self.updateaction_viewurl(request=request,
                                                isstart=True,
                                                context_uid=str(context_oid),
                                                pd_id=action.node.process.id,
                                                action_id=action.node.__name__,
                                                behavior_id=action.behavior_id)
        informations = {}
        informations.update({'action':action,
                             'action_id':action_id,
                             'actionurl_update': actionurl_update,
                             'actionurl_after':after_url})

        return informations

    def afterexecution_viewurl(self, request=None, **args):
        if request is None:
            request = get_current_request()

        args['op'] = 'after_execution_action'
        return request.resource_url(request.context, 
                                   '@@dace-ui-api-view', 
                                   query=args)

    def updateaction_viewurl(self, request=None, **args):
        if request is None:
            request = get_current_request()

        args['op'] = 'update_action'
        return request.resource_url(request.context, 
                                    '@@dace-ui-api-view', 
                                    query=args)

    def _processes(self, view, processes):
        allprocesses = []
        nb_encours = 0
        nb_bloque = 0
        nb_termine = 0
        for process in processes:
            bloced = not process.getWorkItems()
            processe = {'url':view.request.resource_url(process, '@@index'),
                        'process':process, 
                        'bloced':bloced, 
                        'created_at': process.created_at}
            allprocesses.append(processe)
            if process._finished:
                nb_termine += 1
            elif bloced:
                nb_bloque += 1
            else:
                nb_encours += 1

        return nb_encours, nb_bloque, nb_termine, allprocesses

    def update_processes(self, view, processes, tabid):
        result = {}
        processes = sorted(processes, key=lambda p: p.created_at)
        page, pages, processes = calculatePage(processes, view, tabid)
        nb_encours, nb_bloque, nb_termine, allprocesses = self._processes(view, processes)
        values = {'processes': allprocesses,
                  'encours':nb_encours,
                  'bloque':nb_bloque,
                  'termine':nb_termine,
                  'tabid':tabid,
                  'page': page,
                  'pages': pages,
                  'url': view.request.resource_url(view.context, '@@'+view.name)}
        body = view.content(result=values, template='pontus:dace_ui_extension/templates/runtime_view.pt')['body']
        item = view.adapt_item(body, view.viewid)
        result['coordinates'] = {view.coordinates:[item]}
        result  = merge_dicts(view.requirements, result)
        return result

    def statistic_processes(self, view, processes, tabid):
        nb_encours, nb_bloque, \
        nb_termine, allprocesses =  self._processes(view, processes)

        blocedprocesses = [p['process'] for p in  allprocesses \
                           if p['bloced'] and not p['process']._finished ]
        terminetedprocesses = [p['process'] for p in  allprocesses \
                               if p['process']._finished]
        activeprocesses = [p['process'] for p in  allprocesses \
                           if  not p['process']._finished and not p['bloced']]

        result_bloced_runtime_v = self.update_processes(
                               view, blocedprocesses, tabid+'BlocedProcesses')
        item = result_bloced_runtime_v['coordinates'][view.coordinates][0]
        bloques_body = item['body']

        result_encours_runtime_v = self.update_processes(
                                  view, activeprocesses, tabid+'RunProcesses')
        item = result_encours_runtime_v['coordinates'][view.coordinates][0]
        encours_body = item['body']

        result_termines_runtime_v = self.update_processes(
                        view, terminetedprocesses, tabid+'TerminetedProcesses')
        item = result_termines_runtime_v['coordinates'][view.coordinates][0]
        termines_body = item['body']
        values = {'encours':nb_encours,
                  'bloque':nb_bloque,
                  'termine':nb_termine,
                  'terminesBody':termines_body,
                  'encoursBody':encours_body,
                  'bloquesBody':bloques_body
                }
        return values

    def statistic_dates(self, view, processes):
        dates = {}
        for process in processes:
            created_at = process.created_at
            date = str(datetime.datetime(created_at.year, created_at.month, 
                                         created_at.day, created_at.hour, 
                                         created_at.minute))
            if date in dates:
                dates[date] += 1
            else:
                dates[date] = 1

        dates = sorted(dates.items(), key=lambda i: i[0])
        return dates

    def get_action_body(self, context, request, action, add_action_discriminator=False):
        body = ''
        if action is not None:
            view = DEFAULTMAPPING_ACTIONS_VIEWS[action._class_]
            view_instance = view(context, request, behaviors=[action])
            if add_action_discriminator:
                action_oid = get_oid(action)
                view_instance.viewid += str(action_oid)
 
            view_result = view_instance()
            body = ''
            if isinstance(view_result, dict) and 'coordinates' in view_result:
                body = view_instance.render_item(view_result['coordinates'][view_instance.coordinates][0], 
                                                 view_instance.coordinates, None)

        return body


@view_config(name='dace-ui-api-view', 
             context=Entity, 
             xhr=True, 
             renderer='json')
class DaceUIAPIJson(BasicView):

    def _get_start_action(self):
        action = None
        pd_id = self.params('pd_id')
        action_id = self.params('action_id')
        behavior_id = self.params('behavior_id')
        def_container = find_service('process_definition_container')
        pd = def_container.get_definition(pd_id)
        start_wi = pd.start_process(action_id)[action_id]
        for start_action in start_wi.actions:
            if start_action.behavior_id == behavior_id:
                action = start_action
                break

        return action

    def update_action(self, action=None, context=None):
        result = {}
        action_uid = self.params('action_uid')
        try:
            if action_uid is not None:
                action = get_obj(int(action_uid ))
            else:
                action = self._get_start_action()
        except Exception:
            return {}#message erreur

        context_uid = self.params('context_uid')
        try:
            if context_uid is not None:
                context = get_obj(int(context_uid))
        except Exception:
            pass

        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,
                                                      'dace_ui_api')
        result['body'] = dace_ui_api.get_action_body(context, 
                                          self.request, action)
        return result

    def after_execution_action(self):
        action_uid = self.params('action_uid')
        context_uid = self.params('context_uid')
        action = None
        context = None
        try:
            if action_uid is not None:
                action = get_obj(int(action_uid ))
            else:
                action = self._get_start_action()

        except Exception:
            return {}#message erreur

        try:
            if context_uid is not None:
                context = get_obj(int(context_uid))
        except Exception:
            pass

        if action is not None and action.validate(context, self.request):
            action.after_execution(context, self.request)

        return {}#message erreur

    #autres operations
    def __call__(self):
        operation_name = self.params('op')
        if operation_name is not None:
            operation = getattr(self, operation_name, None)
            if operation is not None:
                return operation()

        return {}#message erreur
