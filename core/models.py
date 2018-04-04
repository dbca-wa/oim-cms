from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.core import management
from django.db import models
from django.http import HttpResponseRedirect
from django.utils import timezone
import hashlib
from ipware.ip import get_ip
import logging
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

from organisation.models import DepartmentUser

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


class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    department_user = models.ForeignKey(DepartmentUser, on_delete=models.PROTECT, null=True)
    session = models.ForeignKey(Session, on_delete=models.PROTECT)
    ip = models.GenericIPAddressField(null=True)

    @property
    def shared_id(self):
        return hashlib.sha256('{}{}{}'.format(
            timezone.now().month, self.user.email, settings.SECRET_KEY).lower().encode('utf-8')).hexdigest()


def user_logged_in_handler(sender, request, user, **kwargs):
    logging.debug('user_logged_in_handler')
    request.session.save()
    usersession, created = UserSession.objects.get_or_create(user=user, session_id=request.session.session_key)
    usersession.ip = get_ip(request)
    if DepartmentUser.objects.filter(email__iexact=user.email).exists():
        logging.debug('user_logged_in_handler departmentuser {}'.format(user.email))
        usersession.department_user = DepartmentUser.objects.filter(email__iexact=user.email)[0]
        if (user.username != usersession.department_user.username):
            test = get_user_model().objects.filter(username=usersession.department_user.username)
            if test.exists():
                test.delete()
            user.username = usersession.department_user.username
            user.save()
    usersession.save()
    logging.debug('user_logged_in_handler saving stuff')
    management.call_command("clearsessions", verbosity=0)

user_logged_in.connect(user_logged_in_handler)


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
        subject = request.POST.get('Subject', "OIM Extranet Form")
        postdata = sorted(request.POST.items())
        email = render(request, "emailform.html", {"subject": subject, "email": True, "postdata": postdata}).content
        send_mail(
            '{} ( {} )'.format(subject, request.path), email, 'OIM Extranet <oimsupport@dbca.wa.gov.au>',
            [request.user.email], html_message=email, fail_silently=False)
        response = render(request, "emailform.html", {"subject": subject, "postdata": postdata})
        return response
