from rest_framework import serializers, viewsets, status, generics
from models import Record, Style
from rest_framework.response import Response
import base64
from django.core.files.base import ContentFile
import md5
import base64
from django.views.decorators.csrf import csrf_exempt
import os

# Style Serializer
class StyleSerializer(serializers.ModelSerializer):
    raw_content = serializers.SerializerMethodField(read_only=True)
    content = serializers.CharField(write_only=True,allow_null=True)
    class Meta:
        model = Style
        fields = (
            'name',
            'format',
            'default',
            'content',
            'raw_content'
        )
    def get_raw_content(self, obj):
        if obj.content:
            return obj.content.read().encode('base64')
        else:
            return None

# Record Serializer
class RecordSerializer(serializers.ModelSerializer):
    styles = StyleSerializer(many=True)
    workspace =  serializers.CharField(max_length=255, write_only=True)
    name = serializers.CharField(max_length=255, write_only=True)
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
            'workspace',
            'name',
            'auto_update',
        )

class RecordViewSet(viewsets.ModelViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer
    authentication_classes =[]
    
    def createStyle(self,content):
        uploaded_style = ContentFile(content)
        return uploaded_style
    
    def calculate_checksum(self, content):
        checksum = md5.new()
        checksum.update(content)
        return base64.b64encode(checksum.digest())
        
    
    def create(self,request):
        serializer = RecordSerializer(data=request.data, many=True)
        if serializer.is_valid():
            for uploaded_record in serializer.validated_data:
                uploaded_record = dict(uploaded_record)
                try:
                    # # Check if workspace and name match identifier for a particular record
                    record = Record.objects.get(identifier='{0}:{1}'.format(uploaded_record['workspace'],uploaded_record['name']))
                    # Get all styles associated with the record
                    record_styles = record.styles.all()
                    # Check if the auto update flag is set to true so as to update the record
                    if record.auto_update:
                        # Update the record metadata
                        record.title = uploaded_record['title'],
                        record.any_text = uploaded_record['any_text'],
                        record.abstract = uploaded_record['abstract'],
                        record.keywords = uploaded_record['keywords'],
                        record.bounding_box = uploaded_record['bounding_box'],
                        record.crs = uploaded_record['crs'],
                        if uploaded_record['publication_date']:
                            record.publication_date = uploaded_record['publication_date'],
                        record.service_type = uploaded_record['service_type'],
                        record.links = uploaded_record['links']
                        record.auto_update = uploaded_record['auto_update']
                        record.save()
                        # Update the styles if they need to be updated
                        styles = []
                        for style in uploaded_record['styles']:
                            style = dict(style)
                            try:
                                content = style['content'].decode('base64')
                                new_style = Style(
                                                record = record,
                                                name=style['name'],
                                                format = style['format'],
                                                default = style['default'],
                                                content = self.createStyle(content),
                                            )
                                new_style.raw_data = content
                                styles.append(new_style)
                            except:
                                pass
                        for record_style in record_styles:
                            for style in styles:
                                # Check if a style with the same name exists for the record
                                if record_style.name == style.name and record_style.format == style.format:
                                    # Check the checksum of the two styles to see if they match
                                    if record_style.checksum == self.calculate_checksum(style.raw_data):
                                        pass
                                    else:
                                        # Change the content of the style file
                                        record_style.content = style.content
                                        record_style.save(update_style_file=True)
                                    # Remove the style from the list in order to make the list smaller    
                                    styles.remove(style)
                        # Create all other styles that were not matched to the records styles
                        for style in styles:
                            style.save()
                    else:
                        pass
                except Record.DoesNotExist:
                    # If the record does not exist create a new record
                    record = Record(
                        identifier='{0}:{1}'.format(uploaded_record['workspace'],uploaded_record['name']),
                        title = uploaded_record['title'],
                        any_text = uploaded_record['any_text'],
                        abstract = uploaded_record['abstract'],
                        keywords = uploaded_record['keywords'],
                        bounding_box = uploaded_record['bounding_box'],
                        crs = uploaded_record['crs'],
                        publication_date = uploaded_record['publication_date'],
                        service_type = uploaded_record['service_type'],
                        links = uploaded_record['links']
                    )
                    record.save()
                    styles = uploaded_record['styles']
                    for style in styles:
                        style = dict(style)
                        if style['content']:
                            # Decode the content from base64
                            content = style['content'].decode('base64')
                            new_style = Style(
                                    record = record,
                                    name=style['name'],
                                    format = style['format'],
                                    default = style['default'],
                                    content = self.createStyle(content)
                                )
                            new_style.save()
                            
            queryset = self.get_queryset()
            serializer = RecordSerializer(queryset, many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response({'unsuccessful'},status=status.HTTP_400_BAD_REQUEST)

                    