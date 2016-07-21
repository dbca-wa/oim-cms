from django.conf import settings


def template_context(request):
    """Pass extra context variables to every template.
    """
    context = {
        'application_version': settings.APPLICATION_VERSION,
    }
    context.update(settings.STATIC_CONTEXT_VARS)
    return context
