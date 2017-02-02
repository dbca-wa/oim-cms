from wagtailtinymce.rich_text import TinyMCERichTextArea
from django.utils import translation
translation.activate('en')

class CustomTinyMCERichTextArea(TinyMCERichTextArea):

    def __init__(self, attrs=None, **kwargs):
        super(CustomTinyMCERichTextArea, self).__init__(attrs)
        # NOTE: enable TinyMCE plugins in core/wagtail_hooks.py
        self.kwargs = {
			'buttons': [
				[
					 ['undo', 'redo'],
					 ['styleselect'],
					 ['bold', 'italic'],
					 ['forecolor', 'backcolor'],
					 ['alignleft', 'aligncenter', 'alignright', 'alignjustify'],
					 ['bullist', 'numlist', 'outdent', 'indent'],
					 ['table'],
					 ['link', 'unlink'],
					 ['wagtailimage', 'wagtailembed'],
					 ['pastetext', 'fullscreen'],
					 ['code']
				]
		    ],
			'height': '1000',
			'menus': False,
			'options': {
							'browser_spellcheck': True,
							'noneditable_leave_contenteditable': True,
							'language_load': True,
							'valid_elements': '*[*]',
							'extended_valid_elements':'script[language|type|src],div,table',
							'language': 'en'
						},
			'valid_elements': '*[*]',
			'extended_valid_elements' :'script[language|type|src],div,table',
			'allow_unsafe_link_target': True,
		 }
