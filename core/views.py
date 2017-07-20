from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from ipware.ip import get_ip
import json
import base64
import hashlib
import adal
from wagtail.wagtailcore.models import PageRevision
from wagtail.wagtailsearch.models import Query

from core.models import Content, UserSession
from oim_cms.api import WhoAmIResource
from django.contrib.auth.models import User
from tracking.models import DepartmentUser


def force_email(username):
    if username.find("@") == -1:
        candidates = User.objects.filter(
            username__iexact=username)
        if not candidates:
            return None
        return candidates[0].email
    return username


def adal_authenticate(email, password):
    try:
        context = adal.AuthenticationContext(settings.AZUREAD_AUTHORITY)
        token = context.acquire_token_with_username_password(
            settings.AZUREAD_RESOURCE, email, password,
            settings.SOCIAL_AUTH_AZUREAD_OAUTH2_KEY,
            settings.SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET
        )

    except adal.adal_error.AdalError:
        return None

    candidates = User.objects.filter(email__iexact=token['userId'])
    if candidates.exists():
        return candidates[0]
    else:
        return None


def shared_id_authenticate(email, shared_id):
    us = UserSession.objects.filter(user__email__iexact=email).order_by('-session__expire_date')
    if (not us.exists()) or (us[0].shared_id != shared_id):
        return None
    return us[0].user


@csrf_exempt
def auth_get(request):
    # If user is using SSO, do a normal auth check.
    if request.user.is_authenticated():
        return auth(request)

    if 'sso_user' in request.GET and 'sso_shared_id' in request.GET:
        user = shared_id_authenticate(request.GET.get('sso_user'),
            request.GET.get('sso_shared_id'))
        if user:
            response = HttpResponse(json.dumps(
                {'email': user.email, 'shared_id': request.GET.get('sso_shared_id')
                }), content_type='application/json')
            response["X-email"] = user.email
            response["X-shared-id"] = request.GET.get('sso_shared_id')
            return response

    return HttpResponseForbidden()


@csrf_exempt
def auth_dual(request):
    # If user has a SSO cookie, do a normal auth check.
    if request.user.is_authenticated():
        return auth(request)

    # else return an empty response
    response = HttpResponse('{}', content_type='application/json')
    return response


@csrf_exempt
def auth_ip(request):
    # Get the IP of the current user, try and match it up to a session.
    current_ip = get_ip(request)

    # If there's a basic auth header, perform a check.
    basic_auth = request.META.get("HTTP_AUTHORIZATION")
    if basic_auth:
        # Check basic auth against Azure AD as an alternative to SSO.
        username, password = base64.b64decode(
            basic_auth.split(" ", 1)[1].strip()).decode('utf-8').split(":", 1)
        username = force_email(username)
        user = shared_id_authenticate(username, password)

        if not user:
            user = adal_authenticate(username, password)

        if user:
            response = HttpResponse(json.dumps(
                {'email': user.email, 'client_logon_ip': current_ip}), content_type='application/json')
            response["X-email"] = user.email
            response["X-client-logon-ip"] = current_ip
            return response

    # If user has a SSO cookie, do a normal auth check.
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

    response = HttpResponse(json.dumps(headers), content_type='application/json')
    for key, val in headers.items():
        key = "X-" + key.replace("_", "-")
        response[key] = val

    return response


@csrf_exempt
def auth(request):
    # grab the basic auth data from the request
    basic_auth = request.META.get("HTTP_AUTHORIZATION")
    basic_hash = hashlib.sha1(basic_auth.encode('utf-8')).hexdigest() if basic_auth else None

    # store the access IP in the current user session
    if request.user.is_authenticated():
        try:
            usersession = UserSession.objects.get(
                session_id=request.session.session_key)
        except UserSession.DoesNotExist:
            # If the user does not have a UserSession, log them out and return 401 Unauthorised.
            logout(request)
            return HttpResponse('Unauthorized', status=401)
        current_ip = get_ip(request)
        if usersession.ip != current_ip:
            usersession.ip = current_ip
            usersession.save()

    # check the cache for a match for the basic auth hash
    if basic_hash:
        cachekey = "auth_cache_{}".format(basic_hash)
        content = cache.get(cachekey)
        if content:
            response = HttpResponse(content[0], content_type='application/json')
            for key, val in content[1].items():
                response[key] = val
            response["X-auth-cache-hit"] = "success"

            # for a new session using cached basic auth, reauthenticate
            if not request.user.is_authenticated():
                user = User.objects.get(email__iexact=content[1]['X-email'])
                user.backend = "django.contrib.auth.backends.ModelBackend"
                login(request, user)
            return response

    # check the cache for a match for the current session key
    cachekey = "auth_cache_{}".format(request.session.session_key)
    content = cache.get(cachekey)
    # return a cached response ONLY if the current session has an authenticated user
    if content and request.user.is_authenticated():
        response = HttpResponse(content[0], content_type='application/json')
        for key, val in content[1].items():
            response[key] = val
        response["X-auth-cache-hit"] = "success"
        return response

    cache_basic = False
    if not request.user.is_authenticated():
        # Check basic auth against Azure AD as an alternative to SSO.
        try:
            if basic_auth is None:
                raise Exception('Missing credentials')
            username, password = base64.b64decode(
                basic_auth.split(" ", 1)[1].strip()).decode('utf-8').split(":", 1)
            username = force_email(username)

            # first check for a shared_id match
            # if yes, provide a response, but no session cookie
            # (hence it'll only work against certain endpoints)
            user = shared_id_authenticate(username, password)
            if user:
                response = HttpResponse(json.dumps(
                    {'email': user.email, 'shared_id': password
                    }), content_type='application/json')
                response["X-email"] = user.email
                response["X-shared-id"] = password
                return response

            # after that, check against Azure AD
            user = adal_authenticate(username, password)
            # basic auth using username/password will generate a session cookie
            if user:
                user.backend = "django.contrib.auth.backends.ModelBackend"
                login(request, user)
                cache_basic = True
            else:
                raise Exception('Authentication failed')
        except Exception as e:
            response = HttpResponse(status=401)
            response[
                "WWW-Authenticate"] = 'Basic realm="Please login with your username or email address"'
            response.content = str(e)
            return response

    response_data = WhoAmIResource.as_detail()(request).content
    response = HttpResponse(response_data, content_type='application/json')
    headers = json.loads(response_data.decode('utf-8'))
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

    # cache response
    cache_headers = dict()
    for key, val in headers.items():
        key = "X-" + key.replace("_", "-")
        cache_headers[key], response[key] = val, val
    # cache authentication entries
    if basic_hash and cache_basic:
        cache.set("auth_cache_{}".format(basic_hash), (response.content, cache_headers), 3600)
    cache.set("auth_cache_{}".format(request.session.session_key), (response.content, cache_headers), 3600)

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
