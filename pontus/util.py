# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi

"""Result-merging rules and small lookups.

``merge_dicts`` (with the list/dict rules) is the composition engine
behind the view result contract; ``update_resources`` accumulates the
js/css links on the request; ``get_view`` resolves a registered
Pyramid view by name.
"""
from zope.interface import providedBy

from pyramid.interfaces import IViewClassifier, IView
from pyramid.threadlocal import get_current_registry
map_ = map      # pyramid.compat.map_ (removed in pyramid 2) was the py2/3 alias


def get_copy_fn(obj):
    """Copy function for ``obj`` (list/dict deep-ish copy, identity otherwise)."""
    def default(obj):
        return obj

    return copy_rules.get(obj.__class__, default)


def copy_list(obj):
    """Copy a list, copying its items by rule."""
    return [get_copy_fn(item)(item) for item in list(obj)]


def copy_dict(obj):
    """Copy a dict, copying its values by rule."""
    result = obj.copy()
    for key, value in result.items():
        result[key] = get_copy_fn(value)(value)

    return result


def get_merge_fn(obj):
    """Merge function for ``obj`` (lists extend, dicts recurse), or ``None``."""
    return merge_rules.get(obj.__class__, None)


def merge_list(source, target):
    """Merge: extend ``target`` with ``source``."""
    target.extend(source)
    return target


def merge_dicts(source, target, keys=()):
    """Deep merge ``source`` into a copy of ``target`` (optionally only ``keys``)."""
    selected_dict = source
    if keys:
        selected_dict = {}
        for key in keys:
            if key in source:
                selected_dict[key] = source[key]

    if not selected_dict:
        return target

    target_copy = get_copy_fn(target)(target)
    source_copy = get_copy_fn(selected_dict)(selected_dict)
    for key in source_copy.keys():
        if key in target_copy.keys():
            fn_merge = get_merge_fn(target_copy[key])
            if fn_merge:
                target_copy[key] = fn_merge(source_copy[key],
                                            target_copy[key])
        else:
            target_copy[key] = source_copy[key]

    return target_copy


def update_resources(request, resources={'js_links': [], 'css_links': []}):
    """Accumulate ``js_links``/``css_links`` on ``request.resources``."""
    old_resources = getattr(
        request, 'resources', {'js_links': [], 'css_links': []})
    old_resources['js_links'].extend(resources.get('js_links', []))
    old_resources['css_links'].extend(resources.get('css_links', []))
    request.resources = old_resources


def get_view(context, request, view_name):
    """Resolve the registered view ``view_name`` for (context, request)."""
    provides = [IViewClassifier] + map_(providedBy, (request, context))
    try:
        reg = request.registry
    except AttributeError:
        reg = get_current_registry()

    view = reg.adapters.lookup(provides, IView, name=view_name)
    if view is None:
        return None

    return view


merge_rules = {
    list: merge_list,
    dict: merge_dicts
}

copy_rules = {
    list: copy_list,
    dict: copy_dict
}
