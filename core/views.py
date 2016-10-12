from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django_auth_ldap.backend import LDAPBackend
from ipware.ip import get_ip
import json
from wagtail.wagtailcore.models import PageRevision
from wagtail.wagtailsearch.models import Query

from core.models import Content, UserSession
from oim_cms.api import WhoAmIResource
from tracking.models import DepartmentUser


@csrf_exempt
def auth_ip(request):
    # Get the IP of the current user, try and match it up to a session.
    current_ip = get_ip(request)

    # If there's a basic auth header, perform a check.
    basic_auth = request.META.get("HTTP_AUTHORIZATION")
    if basic_auth:
        # Check basic auth against LDAP as an alternative to SSO.
        username, password = request.META["HTTP_AUTHORIZATION"].split(
            " ", 1)[1].strip().decode('base64').split(":", 1)
        ldapauth = LDAPBackend()
        if username.find("@") > -1:
            username = DepartmentUser.objects.get(
                email__iexact=username).username
        user = ldapauth.authenticate(username=username,
                                     password=password)
        if not user:
            us = UserSession.objects.filter(user__username=username)[0]
            assert us.shared_id == password
            user = us.user

        if user:
            response = HttpResponse(json.dumps(
                {'email': user.email, 'client_logon_ip': current_ip}))
            response["X-email"] = user.email
            response["X-client-logon-ip"] = current_ip
            return response

    # If user is using SSO, do a normal auth check.
    if request.user.is_authenticated():
        return auth(request)

    # We can assume that the Session and UserSession tables only contain
    # current sessions.
    qs = UserSession.objects.filter(
        session__isnull=False,
        ip=current_ip).order_by("-session__expire_date")

    headers = {'client_logon_ip': current_ip}

    if qs.exists():
        user = qs[0].user
        headers["email"] = user.email
        try:
            headers["kmi_roles"] = DepartmentUser.objects.get(
                email__iexact=user.email).extra_data.get("KMIRoles", '')
        except:
            headers["kmi_roles"] = ''

    response = HttpResponse(json.dumps(headers))
    for key, val in headers.iteritems():
        key = "X-" + key.replace("_", "-")
        response[key] = val

    return response


@csrf_exempt
def auth(request):
    if request.user.is_authenticated():
        usersession = UserSession.objects.get(
            session_id=request.session.session_key)
        current_ip = get_ip(request)
        if usersession.ip != current_ip:
            usersession.ip = current_ip
            usersession.save()
    cachekey = "auth_cache_{}".format(request.META.get(
        "HTTP_AUTHORIZATION") or request.session.session_key)
    content = cache.get(cachekey)
    if content:
        response = HttpResponse(content[0])
        for key, val in content[1].iteritems():
            response[key] = val
        response["X-auth-cache-hit"] = "success"
        return response
    if not request.user.is_authenticated():
        # Check basic auth against LDAP as an alternative to SSO.
        try:
            assert request.META.get("HTTP_AUTHORIZATION") is not None
            username, password = request.META["HTTP_AUTHORIZATION"].split(
                " ", 1)[1].strip().decode('base64').split(":", 1)
            ldapauth = LDAPBackend()
            if username.find("@") > -1:
                username = DepartmentUser.objects.get(
                    email__iexact=username).username
            user = ldapauth.authenticate(username=username,
                                         password=password)
            if not user:
                us = UserSession.objects.filter(user__username=username)[0]
                assert us.shared_id == password
                user = us.user
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)
        except Exception as e:
            response = HttpResponse(status=401)
            response[
                "WWW-Authenticate"] = 'Basic realm="Please login with your username or email address"'
            response.content = repr(e)
            return response
    response = HttpResponse(WhoAmIResource.as_detail()(request).content)
    headers, cache_headers = json.loads(response.content), dict()
    headers["full_name"] = u"{}, {}".format(
        headers.get(
            "last_name", ""), headers.get(
            "first_name", ""))
    # TODO: use url reverse on logout alias
    headers["logout_url"] = "https://oim.dpaw.wa.gov.au/logout"
    try:
        headers["kmi_roles"] = DepartmentUser.objects.get(
            email__iexact=headers["email"]).extra_data.get(
            "KMIRoles", '')
    except Exception as e:
        headers["kmi_roles"] = ''
    for key, val in headers.iteritems():
        key = "X-" + key.replace("_", "-")
        cache_headers[key], response[key] = val, val
    cache.set(cachekey, (response.content, cache_headers), 3600)
    return response


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(
        "https://login.windows.net/common/oauth2/logout")


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


def error404(request):
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
