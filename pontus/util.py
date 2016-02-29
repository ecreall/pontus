# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi


def get_copy_fn(obj):
    def default(obj):
        return obj

    return copy_rules.get(obj.__class__, default)


def copy_list(obj):
    return [get_copy_fn(item)(item) for item in list(obj)]


def copy_dict(obj):
    result = obj.copy()
    for key, value in result.items():
        result[key] = get_copy_fn(value)(value)

    return result


def get_merge_fn(obj):
    return merge_rules.get(obj.__class__, None)


def merge_list(source, target):
    target.extend(source)
    return target


def merge_dicts(source, target, keys=()):
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
    old_resources = getattr(
        request, 'resources', {'js_links': [], 'css_links': []})
    old_resources['js_links'].extend(resources.get('js_links', []))
    old_resources['css_links'].extend(resources.get('css_links', []))
    request.resources = old_resources


merge_rules = {
    list: merge_list,
    dict: merge_dicts
}

copy_rules = {
    list: copy_list,
    dict: copy_dict
}
