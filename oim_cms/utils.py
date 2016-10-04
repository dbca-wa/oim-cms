from django.http import HttpResponse
from djqscsv import render_to_csv_response
from restless.dj import DjangoResource


class CSVDjangoResource(DjangoResource):
    """Extend the restless DjangoResource class to add a CSV export endpoint.
    """
    @classmethod
    def as_csv(cls, request):
        resource = cls()
        if not hasattr(resource, "list_qs"):
            return HttpResponse(
                "list_qs not implemented for {}".format(cls.__name__))
        resource.request = request
        return render_to_csv_response(
            resource.list_qs(), field_order=resource.VALUES_ARGS)
