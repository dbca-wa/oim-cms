from django import template
from django.shortcuts import render_to_response
import re
import json

register = template.Library()


@register.filter
def get_excerpt(page):
    result = render_to_response('core/tags/include_content.html', context={
        "self":page,
        "embed":True})
    return result.content


@register.inclusion_tag('core/tags/include_content.html', takes_context=True)
def include_content(context, value):
    from core.models import Content
    try:
        page = Content.objects.get(slug=value)
    except Exception as e:
        page = None
        context.update({"error": "{}: {}".format(value, e)})
    context.update({"self": page})
    return context


@register.inclusion_tag('core/tags/content_list.html', takes_context=True)
def content_list(context, value):
    from core.models import Content
    try:
        val = json.loads(value)
        tags, limit = val["tags"].split(","), int(val["limit"])
        if not tags[0]: # if tags is blank string return all items
            pages = Content.objects.all()[:limit]
        else:
            pages = Content.objects.filter(tags__name__in=tags).distinct()[:limit]
    except Exception as e:
        pages = None
        context.update({"error": "{}: {}".format(value, e)})
    context.update({"pages": pages})
    return context


@register.simple_tag(takes_context=True)
def get_site_root(context):
    # NB this returns a core.Page, not the implementation-specific model used
    # so object-comparison to self will return false as objects would differ
    return context['request'].site.root_page


def has_menu_children(page):
    return page.get_children().live().in_menu().exists()


@register.simple_tag()
def page_menuitems(x):
    menuitems = []
    while x:
        menuitems.append(x)
        x = x.get_parent()

    menuitems.pop()
    menuitems.reverse()
    return menuitems

@register.inclusion_tag('core/tags/breadcrumbs.html', takes_context=True)
def breadcrumbs(context, calling_page):
    x = calling_page
    menuitems = []
    while x:
        menuitems.append(x)
        x = x.get_parent()

    menuitems.pop()
    menuitems.reverse()
    return {
        'menuitems': menuitems,
        'request': context['request']
    }


# Retrieves the top menu items - the immediate children of the parent page
# The has_menu_children method is necessary because the bootstrap menu requires
# a dropdown class to be applied to a parent
@register.inclusion_tag('core/tags/f6_top_menu.html', takes_context=True)
def f6_top_menu(context, parent, calling_page=None):
    menuitems = parent.get_children().live().in_menu()
    for menuitem in menuitems:
        menuitem.show_dropdown = has_menu_children(menuitem)
        # We don't directly check if calling_page is None since the template
        # engine can pass an empty string to calling_page
        # if the variable passed as calling_page does not exist.
        menuitem.active = (calling_page.url.startswith(menuitem.url)
                           if calling_page else False)
    return {
        'calling_page': calling_page,
        'menuitems': menuitems,
        # required by the pageurl tag that we want to use within this template
        'request': context['request'],
    }

# Retrieves the top menu items - the immediate children of the parent page
# The has_menu_children method is necessary because the bootstrap menu requires
# a dropdown class to be applied to a parent
@register.inclusion_tag('core/tags/top_menu.html', takes_context=True)
def top_menu(context, parent, calling_page=None):
    menuitems = parent.get_children().live().in_menu()
    for menuitem in menuitems:
        menuitem.show_dropdown = has_menu_children(menuitem)
        # We don't directly check if calling_page is None since the template
        # engine can pass an empty string to calling_page
        # if the variable passed as calling_page does not exist.
        menuitem.active = (calling_page.url.startswith(menuitem.url)
                           if calling_page else False)
    return {
        'calling_page': calling_page,
        'menuitems': menuitems,
        # required by the pageurl tag that we want to use within this template
        'request': context['request'],
    }


# Retrieves the children of the top menu items for the drop downs
@register.inclusion_tag('core/tags/f6_top_menu_children.html', takes_context=True)
def f6_top_menu_children(context, parent, vertical):
    menuitems_children = parent.get_children().live().in_menu()

    #This would help to create multilevel nav bars
    for menuitem in menuitems_children:
        menuitem.show_dropdown = has_menu_children(menuitem)

    return {
        'vertical': vertical,
        'parent': parent,
        'menuitems_children': menuitems_children,
        # required by the pageurl tag that we want to use within this template
        'request': context['request'],
    }

# Retrieves the children of the top menu items for the drop downs
@register.inclusion_tag('core/tags/top_menu_children.html', takes_context=True)
def top_menu_children(context, parent):
    menuitems_children = parent.get_children().live().in_menu()

    #This would help to create multilevel nav bars
    for menuitem in menuitems_children:
        menuitem.show_dropdown = has_menu_children(menuitem)

    return {
        'parent': parent,
        'menuitems_children': menuitems_children,
        # required by the pageurl tag that we want to use within this template
        'request': context['request'],
    }

@register.inclusion_tag('core/tags/mobile_menu_children.html', takes_context=True)
def mobile_menu_children(context, parent):
    return top_menu_children(context, parent)
