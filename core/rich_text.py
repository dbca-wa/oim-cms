from wagtailtinymce.rich_text import TinyMCERichTextArea


class CustomTinyMCERichTextArea(TinyMCERichTextArea):

    def __init__(self, attrs=None, **kwargs):
        super(CustomTinyMCERichTextArea, self).__init__(attrs)
        # NOTE: enable TinyMCE plugins in core/wagtail_hooks.py
        self.kwargs['buttons'] = [
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
            ]
        ]
