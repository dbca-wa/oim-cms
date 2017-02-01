from django.conf import settings
from django.utils.html import format_html, format_html_join
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.whitelist import attribute_rule, check_url, allow_without_attributes
from wagtail.wagtailcore import hooks


@hooks.register('insert_editor_js')
def enable_source():
    js_files = [
        'js/tinymce-textcolor-plugin.js',
    ]
    js_includes = format_html_join(
        '\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )
    return js_includes + format_html(
        """
        <script>
            // registerHalloPlugin('hallohtml');
            registerMCEPlugin('textcolor');
			registerMCEPlugin('table');
        </script>
        """
    )



@hooks.register('construct_whitelister_element_rules')
def whitelister_element_rules():
    allow_attr = {'border': True, 'cellpadding': True, 'cellspacing': True, 'style': True, 'width': True, 'border': True,
                  'colspan': True, 'margin-left': True, 'margin-right': True, 'height': True, 'border-color': True,
				  'text-align': True, 'background-color': True, 'vertical-align': True, 'scope': True, 'id': True}
    allow_attr_script = {'src': True, 'type':True}

    return {
	   'div': allow_without_attributes,
       'table' : attribute_rule(allow_attr),
       '[document]': allow_without_attributes,
       'a': attribute_rule({'href': check_url}),
       'b': allow_without_attributes,
       'br': allow_without_attributes,
       'div': attribute_rule(allow_attr),
       'em': attribute_rule(allow_attr),
       'h1': allow_without_attributes,
       'h2': allow_without_attributes,
       'h3': allow_without_attributes,
       'h4': allow_without_attributes,
       'h5': allow_without_attributes,
       'h6': allow_without_attributes,
       'hr': allow_without_attributes,
       'i': allow_without_attributes,
       'img': attribute_rule({'src': check_url, 'width': True, 'height': True,'alt': True}),
       'li': attribute_rule(allow_attr),
       'ol': attribute_rule(allow_attr),
       'p': attribute_rule(allow_attr),
       'strong': attribute_rule(allow_attr),
       'sub': attribute_rule(allow_attr),
       'sup': attribute_rule(allow_attr),
       'ul': attribute_rule(allow_attr),
       'blockquote': attribute_rule(allow_attr),
       'pre': attribute_rule(allow_attr),
       'span': attribute_rule(allow_attr),
       'code': attribute_rule(allow_attr),
       'table': attribute_rule(allow_attr),
       'caption': attribute_rule(allow_attr),
       'tbody': attribute_rule(allow_attr),
       'th': attribute_rule(allow_attr),
       'tr': attribute_rule(allow_attr),
       'td': attribute_rule(allow_attr),
       'script': attribute_rule(allow_attr_script)
       }	

