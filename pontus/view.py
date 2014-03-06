from zope.interface import implements
from zope.interface import providedBy

from pyramid.threadlocal import get_current_registry
from pyramid.interfaces import IView as IV, IViewClassifier
from pyramid import renderers
from pyramid.renderers import get_renderer
from pyramid.path import package_of

from pontus.visual import VisualisableElement
from pontus.interfaces import IView
from pontus.wizard import Step

__emptytemplate__ = 'templates/empty.pt'

class View(VisualisableElement, Step):
    implements(IView)

    viewid = ''
    slot = 'main'

    def __init__(self, context, request, parent=None, wizard=None, index=0, **kwargs):
        VisualisableElement.__init__(self,**kwargs)
        Step.__init__(self, wizard, index)
        self.context = context
        self.request = request
        self.parent = parent
        self.content_resources = None
        self.header_resources = {}
        self.content = None

    def _getresources(self):
        resources = self.updateresources()
        content_resources = resources['content_resources']
        header_resources =  resources['header_resources']
        result = content_resources
        if isinstance(result, dict):
            for k in header_resources.keys():
                result[k] = header_resources[k]

        return content_resources, header_resources, result


    def __call__(self):
        cr, hr, result = self._getresources()
        return result
  
    def updateresources(self,):
        pass

    def content(self, main_template=None):
        registry = get_current_registry()
        context_iface = providedBy(self.context)
        view_deriver = registry.adapters.lookup((IViewClassifier, self.request.request_iface, context_iface), IV, name=self.title, default=None)
        discriminator = view_deriver.__discriminator__().resolve()
        template = registry.introspector.get('templates', discriminator)
        content_resources, header_resources, result = self._getresources()
        if main_template is None:
            main_template = get_renderer(__emptytemplate__).implementation()

        if isinstance(result, dict):
            result['main_template'] = main_template

        renderer = renderers.RendererHelper(
                    name=template.title,
                    package=package_of(self.__class__.__module__),
                    registry = registry)
        response = renderer.render_view(self.request, result, self, self.context)
        return {'body':response.ubody,
                'header_resources':header_resources,
                'content_resources':content_resources
               }

    def setviewid(self, viewid):
        self.viewid = viewid

