from __future__ import unicode_literals
import hashlib
import logging
import os

from django.conf import settings
from django.core import management
from django.db import models
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailsearch import index
from wagtail.wagtailadmin.edit_handlers import FieldPanel, StreamFieldPanel
#from wagtailmarkdown import MarkdownBlock
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from django.http import HttpResponseRedirect

from tracking.models import DepartmentUser

from ipware.ip import get_ip

from wagtail.wagtailimages.formats import Format, register_image_format

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


class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    department_user = models.ForeignKey(DepartmentUser, null=True)
    session = models.ForeignKey(Session)
    ip = models.GenericIPAddressField(null=True)

    @property
    def shared_id(self):
        return hashlib.sha256("{}{}{}".format(
            timezone.now().month, self.user.email, settings.SECRET_KEY).lower()).hexdigest()


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
        ('heading', blocks.CharBlock(classname="full title")),
        ('rich_text', blocks.RichTextBlock()),
        ('raw', blocks.RawHTMLBlock()),
        ('include_content', blocks.CharBlock()),
        ('content_list', blocks.CharBlock()),
    ], null=True, blank=True)
    date = models.DateField("Content updated date", default=timezone.now)
    template_filename = models.CharField(max_length=64, choices=(
        ("content.html", "content.html"),
        ("f6-content.html", "f6-content.html"),
    ), default="content.html")
    tags = ClusterTaggableManager(through=ContentTag, blank=True)

    def get_template(self, request, *args, **kwargs):
        template_name = request.GET.get("template", self.template_filename)
        return "{}/{}".format(self.__class__._meta.app_label, template_name)

    promote_panels = Page.promote_panels + [
        FieldPanel('date'),
        FieldPanel('tags')
    ]

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    settings_panels = Page.settings_panels + [
        FieldPanel("template_filename")
    ]

    search_fields = Page.search_fields + (
        index.SearchField('body'),
        index.FilterField('url_path'),
    )

    def serve(self, request):
        if "draft" in request.GET:
            return HttpResponseRedirect("/admin/pages/{}/view_draft/".format(self.pk))
        response = super(Content, self).serve(request)
        if "embed" in request.GET:
            with open(os.path.join(settings.MEDIA_ROOT, "images", self.slug + ".html")) as output:
                output.write(response.content)
        return response


    class Meta:
        ordering = ("date",)
