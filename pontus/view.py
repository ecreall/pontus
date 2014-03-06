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

    def __call__(self):
        result = self.update()
        if isinstance(result, dict):
            if not ('js_links' in result):
                result['js_links'] = []

            if not ('css_links' in result):
                result['css_links'] = []

        return result
  
    def update(self,):
        pass

    def content(self, main_template=None):
        registry = get_current_registry()
        context_iface = providedBy(self.context)
        view_deriver = registry.adapters.lookup((IViewClassifier, self.request.request_iface, context_iface), IV, name=self.title, default=None)
        discriminator = view_deriver.__discriminator__().resolve()
        template = registry.introspector.get('templates', discriminator)
        result = self()
        if main_template is None:
            main_template = get_renderer(__emptyteheadermplate__).implementation()

        if isinstance(result, dict):
            result['main_template'] = main_template

        renderer = renderers.RendererHelper(
                    name=template.title,
                    package=package_of(self.__class__.__module__),
                    registry = registry)
        response = renderer.render_view(self.request, result, self, self.context)
        return {'body':response.ubody,
                'args':result,
               }

    def setviewid(self, viewid):
        self.viewid = viewid

