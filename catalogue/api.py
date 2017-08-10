import traceback
from rest_framework import serializers, viewsets, status, filters
from rest_framework.response import Response
import base64
from django.core.files.base import ContentFile
import hashlib
import json
from django.conf import settings
from django.db.models.fields.files import FieldFile
from pycsw.core import util

from .models import Record, Style


# Ows Resource Serializer
class OwsResourceSerializer(serializers.Serializer):
    wfs = serializers.BooleanField(write_only=True, default=False)
    wfs_endpoint = serializers.CharField(write_only=True, allow_null=True, default=None)
    wfs_version = serializers.CharField(write_only=True, allow_null=True, default=None)
    wms = serializers.BooleanField(write_only=True, default=False)
    wms_endpoint = serializers.CharField(write_only=True, allow_null=True, default=None)
    wms_version = serializers.CharField(write_only=True, allow_null=True, default=None)
    gwc = serializers.BooleanField(write_only=True, default=False)
    gwc_endpoint = serializers.CharField(write_only=True, allow_null=True, default=None)

    def validate(self, data):
        if ((data['wfs'] and (not data['wfs_endpoint'] or not data['wfs_version'])) or
            (data['wms'] and (not data['wms_endpoint'] or not data['wms_version'])) or
            (data['gwc'] and not data['gwc_endpoint'])):
            raise serializers.ValidationError("Both endpoint and version must have value if service is enabled.")
        elif (data['gwc'] and not data['wms']):
            raise serializers.ValidationError("WMS must be enabled if gwc is enabled.")
        else:
            return data

    def save(self, record=None):
        if record:
            links = []
            if self.validated_data['gwc']:
                gwc_endpoints = [endpoint.strip() for endpoint in self.validated_data['gwc_endpoint'].split("^") if endpoint.strip()]
                for endpoint in gwc_endpoints:
                    links.append(
                        record.generate_ows_link(endpoint, 'GWC', self.validated_data['wms_version'])
                    )
            elif self.validated_data['wms']:
                links.append(
                    record.generate_ows_link(self.validated_data['wms_endpoint'], 'WMS', self.validated_data['wms_version'])
                )
            if self.validated_data['wfs']:
                links.append(
                    record.generate_ows_link(self.validated_data['wfs_endpoint'], 'WFS', self.validated_data['wfs_version'])
                )
            if record.service_type == "WMS":
                record.service_type_version = self.validated_data['wms_version']
            elif record.service_type == "WFS":
                record.service_type_version = self.validated_data['wfs_version']
            else:
                record.service_type_version = ""

            style_links = record.style_links
            resources = links + style_links

            Record.update_links(resources, record)


# Style Serializer
class StyleSerializer(serializers.ModelSerializer):
    content = serializers.CharField(write_only=True, allow_null=True)
    name = serializers.CharField(default=Style.BUILTIN)

    def get_raw_content(self, obj):
        if obj.content:
            return obj.content.read().encode('base64')
        else:
            return None

    def __init__(self, *args, **kwargs):
        try:
            style_content = kwargs.pop("style_content")
        except:
            style_content = False

        super(StyleSerializer, self).__init__(*args, **kwargs)
        if style_content:
            self.fields['raw_content'] = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Style
        fields = (
            'name',
            'format',
            'default',
            'content',
        )


class LegendSerializer(serializers.Serializer):
    content = serializers.CharField(write_only=True, allow_null=False)
    ext = serializers.CharField(write_only=True, allow_null=False)


# Record Serializer
class RecordSerializer(serializers.ModelSerializer):
    workspace = serializers.CharField(max_length=255, write_only=True)
    name = serializers.CharField(max_length=255, write_only=True)
    id = serializers.IntegerField(read_only=True)
    identifier = serializers.CharField(max_length=255, read_only=True)
    url = serializers.SerializerMethodField(read_only=True)
    publication_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S.%f')
    modified = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S.%f', allow_null=True, default=None)
    metadata_link = serializers.SerializerMethodField(read_only=True)
    tags = serializers.SerializerMethodField(read_only=True)
    source_legend = LegendSerializer(write_only=True, allow_null=True, required=False)
    legend = serializers.SerializerMethodField(read_only=True)

    def get_tags(self, obj):
        return obj.tags.values("name", "description")

    def get_ows_resource(self, obj):
        return obj.ows_resource

    def get_metadata_link(self, obj):
        return obj.metadata_link

    def get_legend(self, obj):
        return (obj.legend or obj.source_legend).url if obj.legend or obj.source_legend else None

    def __init__(self, *args, **kwargs):
        try:
            style_content = kwargs.pop("style_content")
        except:
            style_content = False
        try:
            ows_serializer_method = kwargs.pop('ows')
        except:
            ows_serializer_method = 'get'

        super(RecordSerializer, self).__init__(*args, **kwargs)
        self.fields['styles'] = StyleSerializer(many=True, required=False, style_content=style_content)
        if ows_serializer_method == 'post':
            self.fields['ows_resource'] = OwsResourceSerializer(write_only=True, required=False)
        elif ows_serializer_method == 'get':
            self.fields['ows_resource'] = serializers.SerializerMethodField(read_only=True)

    def get_url(self, obj):
        return '{0}/catalogue/api/records/{1}.json'.format(settings.BASE_URL, obj.identifier)

    def legend_file_name(self, source_legend):
        return "{}{}".format(self.instance.identifier.replace(":", "_"), source_legend.get('ext') or "")

    def create(self, validated_data):
        source_legend = validated_data.pop("source_legend") if "source_legend" in validated_data else None
        instance = super(RecordSerializer, self).create(validated_data)
        self.instance = instance
        if source_legend:
            instance.source_legend = FieldFile(self.instance, Record._meta.get_field("source_legend"), self.legend_file_name(source_legend))
            instance.source_legend.save(self.legend_file_name(source_legend), source_legend['content'], save=False)
        return instance

    def update(self, instance, validated_data):
        source_legend = validated_data.pop("source_legend") if "source_legend" in validated_data else None
        if source_legend:
            if instance.source_legend:
                instance.source_legend.delete(save=False)
            instance.source_legend = FieldFile(instance, Record._meta.get_field("source_legend"), self.legend_file_name(source_legend))
            instance.source_legend.save(self.legend_file_name(source_legend), source_legend['content'], save=False)
        elif instance.source_legend:
            instance.source_legend.delete(save=False)

        return super(RecordSerializer, self).update(instance, validated_data)

    class Meta:
        model = Record
        fields = (
            'id',
            'url',
            'identifier',
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
            'ows_resource',
            'metadata_link',
            'styles',
            'workspace',
            'legend',
            'source_legend',
            'name',
            'tags'
        )


class RecordViewSet(viewsets.ModelViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer
    authentication_classes = []
    lookup_field = "identifier"
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ("tags__name", "application__name")

    def calculate_checksum(self, content):
        checksum = hashlib.md5()
        checksum.update(content)
        return base64.b64encode(checksum.digest())

    def perform_destroy(self, instance):
        instance.active = False
        instance.save()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        style_content = bool(request.GET.get("style_content", False))
        serializer = self.get_serializer(instance, style_content=style_content, ows='get')
        return Response(serializer.data)

    def create(self, request):
        try:
            styles_data = None
            ows_data = None
            http_status = status.HTTP_200_OK
            if "styles" in request.data:
                styles_data = request.data.pop("styles")
            if "ows_resource" in request.data:
                ows_data = request.data.pop("ows_resource")
            # parse and valid record data
            serializer = RecordSerializer(data=request.data, ows='post')
            serializer.is_valid(raise_exception=True)
            # parse and valid styles data
            style_serializers = [StyleSerializer(data=style) for style in styles_data] if styles_data else []
            if style_serializers:
                for style_serializer in style_serializers:
                    style_serializer.is_valid(raise_exception=True)
            # parse and vlaidate ows data
            ows_serializer = OwsResourceSerializer(data=ows_data)
            ows_serializer.is_valid(raise_exception=True)
            # save record data.
            identifier = "{}:{}".format(serializer.validated_data['workspace'], serializer.validated_data['name'])
            # transform the bbox data format
            if serializer.validated_data.get('bounding_box'):
                bounding_box = json.loads(serializer.validated_data['bounding_box'])
                bounding_box = ','.join([str(o) for o in bounding_box])
                try:
                    serializer.validated_data['bounding_box'] = util.bbox2wktpolygon(bounding_box)
                except:
                    traceback.print_exc()
                    raise serializers.ValidationError("Incorrect bounding box dataformat.")

            if serializer.validated_data.get("source_legend"):
                serializer.validated_data["source_legend"]["content"] = ContentFile(serializer.validated_data["source_legend"]["content"].decode("base64"))

            try:
                serializer.instance = Record.objects.get(identifier=identifier)
                serializer.instance.active = True
                for key in ["title", "abstract", "modified", "insert_date"]:
                    if key in serializer.validated_data:
                        serializer.validated_data.pop(key)

                # remove fake fields
                if "workspace" in serializer.validated_data:
                    serializer.validated_data.pop("workspace")
                if "name" in serializer.validated_data:
                    serializer.validated_data.pop("name")

                record = serializer.save()
            except Record.DoesNotExist:
                #record does not exist, create it
                serializer.validated_data['identifier'] = identifier
                # remove fake fields
                if "workspace" in serializer.validated_data:
                    serializer.validated_data.pop("workspace")
                if "name" in serializer.validated_data:
                    serializer.validated_data.pop("name")
                record = serializer.save()
                http_status = status.HTTP_201_CREATED
                # set the missing data and transform the content
                for style_serializer in style_serializers:
                    uploaded_style = style_serializer.validated_data
                    uploaded_style["record"] = record
                    uploaded_style["content"] = ContentFile(uploaded_style["content"].decode("base64"))

                # set default style
                origin_default_style = {
                    "sld": record.sld.name if record.sld else None,
                    "qml": record.qml.name if record.qml else None,
                    "lyr": record.lyr.name if record.lyr else None
                }
                default_style = {}
                for style_serializer in style_serializers:
                    uploaded_style = style_serializer.validated_data
                    if uploaded_style.get("default", False):
                        # user set this style as default style, use the user's setting
                        default_style[uploaded_style["format"]] = uploaded_style
                    elif origin_default_style.get(uploaded_style["format"].lower(), None) == uploaded_style["name"]:
                        # the current style is configured default style.
                        default_style[uploaded_style["format"]] = uploaded_style
                    elif not origin_default_style.get(uploaded_style["format"].lower(), None) and uploaded_style["format"] not in default_style:
                        # no default style has been set, set the current style as the default style
                        default_style[uploaded_style["format"]] = uploaded_style
                    # clear the default flag
                    uploaded_style["default"] = False

                # set the default style
                for uploaded_style in default_style.itervalues():
                    uploaded_style["default"] = True

                #save  style
                for style_serializer in style_serializers:
                    style_serializer.save()

            ows_serializer.save(record)

            record.styles = list(Style.objects.filter(record=record))
            style_content = bool(request.GET.get("style_content", False))
            serializer = RecordSerializer(record, style_content=style_content, ows='get')
            return Response(serializer.data, status=http_status)
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError(str(e))
