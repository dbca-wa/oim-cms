from django.conf import settings
from django.db import models
from django.http import HttpResponseRedirect
from django.utils import safestring, timezone
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
import os
from taggit.models import TaggedItemBase
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core import blocks, hooks
from wagtail.core.models import Page
from wagtail.core.fields import StreamField
from wagtail.images.formats import Format, register_image_format
from wagtail.search import index

from django.shortcuts import render
from django.core.mail import send_mail

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
        ('heading', blocks.CharBlock(classname='full title')),
        ('rich_text', blocks.RichTextBlock()),
        ('raw', blocks.RawHTMLBlock()),
        ('include_content', blocks.CharBlock()),
        ('content_list', blocks.CharBlock()),
    ], null=True, blank=True)
    date = models.DateField('Content updated date', default=timezone.now)
    template_filename = models.CharField(max_length=64, choices=(
        ('content.html', 'content.html'),
        ('f6-content.html', 'f6-content.html'),
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


@hooks.register('before_serve_page')
def submit_form(page, request, serve_args, serve_kwargs):

    if request.method == 'POST':
        subject = request.POST.get('Subject', 'OIM Extranet Form')
        postdata = sorted(request.POST.items())
        # Infer any additional instructions based on the request path.
        # HACK: this is tightly coupled to the form submit path :|
        path = request.META['PATH_INFO'].split('/')
        instructions = None
        if 'transfer-user-account' in path:
            instructions = safestring.mark_safe('''
                Please forward this form to the receiving Cost Centre Manager for approval and submission to
                OIM Service Desk (<a href="mailto:oim.servicedesk@dbca.wa.gov.au">oim.servicedesk@dbca.wa.gov.au</a>).
                Authorisation from the previous Cost Centre manager is also required to be attached.
            ''')
        elif 'suspend-user-account' in path:
            instructions = safestring.mark_safe('''
                Please forward this form to the Cost Centre Manager for approval and submission to
                OIM Service Desk (<a href="mailto:oim.servicedesk@dbca.wa.gov.au">oim.servicedesk@dbca.wa.gov.au</a>).
            ''')
        response = render(
            request,
            'emailform.html',
            {'subject': subject, 'email': True, 'postdata': postdata, 'additional_instructions': instructions}
        )
        email = response.content.decode('utf-8')
        send_mail(
            '{} ( {} )'.format(subject, request.path), email, 'OIM Service Desk <oim.servicedesk@dbca.wa.gov.au>',
            [request.user.email], html_message=email, fail_silently=False)
        return response
