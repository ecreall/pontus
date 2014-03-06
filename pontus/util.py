from zope.interface import providedBy
from pyramid.threadlocal import get_current_registry
from pyramid.interfaces import IView, IViewClassifier
from pyramid import renderers
from pyramid.path import package_of

def get_view(context, request, name):
    registry = get_current_registry()
    context_iface = providedBy(context)
    view_deriver = registry.adapters.lookup((IViewClassifier, request.request_iface, context_iface), IView, name=name, default=None)
    view = view_deriver.__original_view__
    discriminator = view_deriver.__discriminator__().resolve()
    import pdb;pdb.set_trace()
    template = registry.introspector.get('templates', discriminator)
    # this must adapt, it can't do a simple interface check
    # (avoid trying to render webob responses)

    view_inst = view(context, request)
    result = view_inst()

    renderer = renderers.RendererHelper(
                name=template.title,
                package=package_of(view.__module__),
                registry = registry)
    response = renderer.render_view(request, result, view_inst, context)

    return response
