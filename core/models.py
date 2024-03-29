from django.conf import settings
from django.db import models
from django.http import HttpResponseRedirect
from django.utils import timezone
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
import os
from taggit.models import TaggedItemBase
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core import blocks
from wagtail.core.models import Page
from wagtail.core.fields import StreamField
from wagtail.images.formats import Format, register_image_format
from wagtail.search import index


'''To add a new size format use the following format
   register_image_format(Format('name', 'label', 'class_names', 'filter_spec'))

   These are the Format arguments:

   name -> unique key used to identify the format
   label -> label used in the chooser form when inserting the image in the RichTextField
   class_names -> string to assign to the class attribute of the generated <img> tag.
   filter_spec -> string specification to create the image rendition.
'''

register_image_format(Format('600x600', '600x600', 'richtext-image 600x600', 'max-600x600'))
register_image_format(Format('logo_icon', 'Logo_Icon', 'richtext-image logo_icon', 'max-30x30'))
register_image_format(Format('original', 'Original', 'richtext-image original', 'original'))


class ContentTag(TaggedItemBase):
    content_object = ParentalKey('core.Content', related_name='tagged_items')


class Content(Page):
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname='full title')),
        ('rich_text', blocks.RichTextBlock()),
        ('raw', blocks.RawHTMLBlock()),
        ('include_content', blocks.CharBlock()),
        ('content_list', blocks.CharBlock()),
    ], null=True, blank=True)
    date = models.DateField('Content updated date', default=timezone.now)
    template_filename = models.CharField(max_length=64, choices=(
        ('content.html', 'content.html'),
        ('f6-content.html', 'f6-content.html'),
        ('f6-content-minimal.html', 'f6-content-minimal.html'),
        ('f6-vue.html', 'f6-vue.html'),
    ), default='f6-content.html')
    tags = ClusterTaggableManager(through=ContentTag, blank=True)

    def get_template(self, request, *args, **kwargs):
        template_name = request.GET.get('template', self.template_filename)
        return '{}/{}'.format(self.__class__._meta.app_label, template_name)

    promote_panels = Page.promote_panels + [
        FieldPanel('date'),
        FieldPanel('tags')
    ]

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    settings_panels = Page.settings_panels + [
        FieldPanel('template_filename')
    ]

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.FilterField('url_path'),
    ]

    def serve(self, request):
        if 'draft' in request.GET:
            return HttpResponseRedirect('/admin/pages/{}/view_draft/'.format(self.pk))
        response = super(Content, self).serve(request)
        if 'embed' in request.GET:
            with open(os.path.join(settings.MEDIA_ROOT, 'images', self.slug + '.html')) as output:
                output.write(response.content)
        return response

    class Meta:
        ordering = ('date',)
