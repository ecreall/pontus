from pyramid.threadlocal import get_current_request

from substanced.sdi import mgmt_view
from substanced.util import get_oid

from dace.util import get_obj, find_service
from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from dace.objectofcollaboration.entity import Entity

from pontus.view import BasicView


class Dace_ui_api(object):

    @classmethod
    def afterexecution_viewurl(cls, request=None, **args):
        if request is None:
            request = get_current_request()

        args['op'] = 'after_execution_action'
        return request.mgmt_path(request.context, '@@dace-ui-api', query=args)

    @classmethod
    def updateaction_viewurl(cls, request=None, **args):
        if request is None:
            request = get_current_request()

        args['op'] = 'update_action'
        return request.mgmt_path(request.context, '@@dace-ui-api', query=args)


@mgmt_view(name='dace-ui-api', context=Entity, xhr=True, renderer='json')
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

    def update_action(self):
        action_uid = self.params('action_uid')
        context_uid = self.params('context_uid')
        action = None
        context = None
        result = {}
        try:
            if action_uid is not None:
                if action_uid != 'start':
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

        if action is not None:
            view = DEFAULTMAPPING_ACTIONS_VIEWS[action._class]
            view_instance = view(context, self.request, behaviors=[action])
            result = view_instance()

            if isinstance(result, dict):
                if 'js_links' in result and result['js_links']:
                    js_links = []
                    for js in result['js_links']:
                        js_links.append(self.request.static_url(js))
           
                result['js_links']
                if 'css_links' in result and result['css_links']:
                    css_links = []
                    for css in result['css_links']:
                        css_links.append(self.request.static_url(css))
           
                result['css_links']
                for coordinate, items in result['coordinates'].iteritems():
                    for item in items:
                        if 'view' in item:
                            item.pop('view')

        return result

    def after_execution_action(self):
        action_uid = self.params('action_uid')
        context_uid = self.params('context_uid')
        action = None
        context = None
        try:
            if action_uid is not None:
                if action_uid != 'start':
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
