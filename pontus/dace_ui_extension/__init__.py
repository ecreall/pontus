import datetime
from math import ceil
from zope.interface import implementer

from pyramid.threadlocal import get_current_request, get_current_registry
from pyramid.view import view_config

from substanced.util import get_oid

from dace.util import get_obj, find_service, utility
from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from dace.objectofcollaboration.entity import Entity

from pontus.view import BasicView, merge_dicts, ViewError
from .interfaces import IDaceUIAPI


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
class Dace_ui_api(object):


    def _modal_views(self, request, all_actions, form_id):
        action_updated=False
        resources = {}
        resources['js_links'] = []
        resources['css_links'] = []
        allbodies_actions = []
        updated_view = None
        for t in all_actions:
            a = t[1]
            c = t[0]
            view = DEFAULTMAPPING_ACTIONS_VIEWS[a.action._class_]
            view_instance = view(c, request, behaviors=[a.action])
            view_result = {}
            if not action_updated and form_id is not None and view_instance.has_id(form_id):
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

                body = ''
                if 'coordinates' in view_result:
                    body = view_instance.render_item(view_result['coordinates'][view_instance.coordinates][0], view_instance.coordinates, None)


                action_infos.update(self.action_infomrations(action=a.action, context=c, request=request))
                action_infos.update({'body':body,
                             'actionurl': a.url,
                             'data': c})
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

    def _actions(self, request, object, process_id=None, action_id=None, process_discriminator=None):
        all_actions = []
        messages = {}
        actions = [a for a in object.actions]
        if process_id is not None:
            actions = [a for a in actions if a.action.process_id == process_id]

        if action_id is not None:
            actions = [a for a in actions if a.action.node_id == action_id]

        if process_discriminator is not None:
            actions = [a for a in actions if a.action.node.process.discriminator == process_discriminator]

        actions = sorted(actions, key=lambda a: getattr(a.action, '__name__', a.action.__class__.__name__))
        p_actions = [(object,a) for a in actions]
        all_actions.extend(p_actions)
        object_oid = str(get_oid(object))
        form_id = None
        if '__formid__' in request.POST:
            if request.POST['__formid__'].find(object_oid)>=0:
                form_id = request.POST['__formid__']

        toreplay, action_updated, resources, allbodies_actions = self._modal_views(request, all_actions, form_id)
        if toreplay:
            request.POST.clear()
            old_resources = resources
            old_allbodies_actions = allbodies_actions
            action_updated, messages, resources, allbodies_actions = self._actions(request, object, process_id, action_id, process_discriminator)
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

        if form_id is not None and not action_updated and all_actions:
            error = ViewError()
            error.principalmessage = u"Action non realisee"
            error.causes = ["Vous n'avez plus le droit de realiser cette action.", "L'action est verrouillee par un autre utilisateur."]
            message = self._get_message(error)
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
        after_url = self.afterexecution_viewurl(request=request, action_uid=str(action_oid), context_uid=str(context_oid))
        actionurl_update = self.updateaction_viewurl(request=request, action_uid=str(action_oid), context_uid=str(context_oid))
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
        return request.resource_url(request.context, '@@dace-ui-api-view', query=args)

    def updateaction_viewurl(self, request=None, **args):
        if request is None:
            request = get_current_request()

        args['op'] = 'update_action'
        return request.resource_url(request.context, '@@dace-ui-api-view', query=args)

    def _processes(self, view, processes):
        allprocesses = []
        nb_encours = 0
        nb_bloque = 0
        nb_termine = 0
        for p in processes:
            bloced = not p.getWorkItems()
            processe = {'url':view.request.resource_url(p, '@@index'), 'process':p, 'bloced':bloced, 'created_at': p.created_at}
            allprocesses.append(processe)
            if p._finished:
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
        result  = merge_dicts(dict(view.requirements), result)
        return result

    def statistic_processes(self, view, processes, tabid):
        nb_encours, nb_bloque, nb_termine, allprocesses =  self._processes(view, processes)

        blocedprocesses = [p['process'] for p in  allprocesses if p['bloced'] and not p['process']._finished ]
        terminetedprocesses = [ p['process'] for p in  allprocesses if p['process']._finished]
        activeprocesses = [ p['process'] for p in  allprocesses if  not p['process']._finished and not p['bloced']]

        result_bloced_runtime_v = self.update_processes(view, blocedprocesses, tabid+'BlocedProcesses')
        item = result_bloced_runtime_v['coordinates'][view.coordinates][0]
        bloquesBody =item['body']

        result_encours_runtime_v = self.update_processes(view, activeprocesses, tabid+'RunProcesses')
        item = result_encours_runtime_v['coordinates'][view.coordinates][0]
        encoursBody =item['body']

        result_termines_runtime_v = self.update_processes(view, terminetedprocesses, tabid+'TerminetedProcesses')
        item = result_termines_runtime_v['coordinates'][view.coordinates][0]
        terminesBody =item['body']
        values = {'encours':nb_encours,
                  'bloque':nb_bloque,
                  'termine':nb_termine,
                  'terminesBody':terminesBody,
                  'encoursBody':encoursBody,
                  'bloquesBody':bloquesBody
                }
        return values

    def statistic_dates(self, view, processes):
        dates = {}
        for p in processes:
            created_at = p.created_at
            date = str(datetime.datetime(created_at.year, created_at.month, created_at.day, created_at.hour, created_at.minute))
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
            if 'coordinates' in view_result:
                body = view_instance.render_item(view_result['coordinates'][view_instance.coordinates][0], view_instance.coordinates, None)

        return body


@view_config(name='dace-ui-api-view', context=Entity, xhr=True, renderer='json')
class Dace_ui_api_json(BasicView):

    def _get_start_action(self):
        action = None
        pd_id = self.params('pd_id')
        action_id = self.params('action_id')
        behavior_id = self.params('behavior_id')
        def_container = find_service('process_definition_container')
        pd = def_container.get_definition(pd_id)
        start_wi = pd.start_process(action_id)
        for a in start_wi.actions:
            if a.behavior_id == behavior_id:
                action = a
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

        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,'dace_ui_api')
        result['body'] = dace_ui_api.get_action_body(context, self.request, action)
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
