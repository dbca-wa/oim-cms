from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from wagtail.core import hooks
from wagtail.core.models import PageRevision
from wagtail.search.models import Query
from core.models import Content


def draft(request, path):
    if len(path) > 1:
        if path[-1] == "/":
            path = path[:-1]
        path = "/" + path + "/"
    else:
        path = "/"
    revisions = PageRevision.objects.filter(
        content_json__icontains='"url_path": "/home{}"'.format(path)).order_by("-created_at")
    if revisions.exists() and revisions[
            0].page.get_latest_revision().pk == revisions[0].pk:
        return HttpResponseRedirect("/admin/pages/{}/view_draft/{}".format(
            revisions[0].page.pk, request.META.get("QUERY_STRING")))
    elif revisions.exists():
        return HttpResponse(
            "No current draft ({} old) exists for url: {}".format(revisions.count(), path))
    else:
        return HttpResponse("No draft exists for url: {}".format(path))


def redirect(request):
    path = request.get_full_path().replace("/redirect/", "", 1)
    return HttpResponseRedirect("https://{}".format(path))


def search_content(search_query):
    # Search
    search_results = Content.objects.live().exclude(
        url_path__startswith="/home/snippets/").search(search_query)
    query = Query.get(search_query)
    # Record hit
    query.add_hit()
    return search_results


def search(request):
    search_query = request.GET.get('q', None)
    if search_query:
        search_results = search_content(search_query)
    else:
        search_results = Content.objects.none()

    return render(request, 'core/search_results.html', {
        'search_results': search_results,
    })


def error404(request, exception=None):
    search_query = " ".join(request.get_full_path().split("/"))
    search_results = search_content(search_query)
    if search_results.count() == 1:
        return HttpResponseRedirect(search_results[0].url)
    else:
        response = HttpResponse(
            content=render(request, 'core/search_results.html', {
                'search_results': search_results,
                'http_error_code': 404
            }).content,
            content_type='text/html; charset=utf-8',
            status=404
        )
        return response


@hooks.register('before_serve_page')
def submit_form(page, request, serve_args, serve_kwargs):

    if request.method == 'POST':
        subject = request.POST.get('Subject', 'OIM Extranet Form')
        postdata = sorted(request.POST.items())
        # Infer any additional instructions based on the request path.
        # HACK: this is tightly coupled to the form submit path :|
        path = request.META['PATH_INFO'].split('/')
        instructions = mark_safe('''
            Please forward this form to the Cost Centre Manager for approval and submission to
            OIM Service Desk (<a href="mailto:oim.servicedesk@dbca.wa.gov.au">oim.servicedesk@dbca.wa.gov.au</a>).
        ''')
        if 'transfer-user-account' in path:
            instructions = mark_safe('''
                Please forward this form to the receiving Cost Centre Manager for approval and submission to
                OIM Service Desk (<a href="mailto:oim.servicedesk@dbca.wa.gov.au">oim.servicedesk@dbca.wa.gov.au</a>).
                Authorisation from the previous Cost Centre manager is also required to be attached.
            ''')
        response = render(
            request,
            'emailform.html',
            {'subject': subject, 'email': True, 'postdata': postdata, 'instructions': instructions}
        )
        email = response.content.decode('utf-8')
        send_mail(
            '{} ( {} )'.format(subject, request.path), email, 'OIM Service Desk <oim.servicedesk@dbca.wa.gov.au>',
            [request.user.email], html_message=email, fail_silently=False)
        return response


class HealthCheckView(TemplateView):
    """A basic template view not requiring auth, used for service monitoring.
    """
    template_name = 'healthcheck.html'

    def get_context_data(self, **kwargs):
        context = super(HealthCheckView, self).get_context_data(**kwargs)
        context['page_title'] = 'OIM CMS application status'
        context['status'] = 'HEALTHY'
        return context
