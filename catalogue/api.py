from rest_framework import serializers, viewsets, status
from models import Record, Style
from rest_framework.response import Response

# Style Serializer
class StyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Style
        fields = (
            'name',
            'format',
            'default'
        )

# Record Serializer
class RecordSerializer(serializers.ModelSerializer):
    styles = StyleSerializer(many=True)
    class Meta:
        model = Record
        fields = (
            'title',
            'insert_date',
            'any_text',
            'modified',
            'abstract',
            'keywords',
            'bounding_box',
            'crs',
            'publication_date',
            'service_type',
            'service_type_version',
            'links',
            'styles',
        )


class RecordViewSet(viewsets.ModelViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer