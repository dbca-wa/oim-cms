from rest_framework import serializers, viewsets, status, generics
from models import Room
from rest_framework.response import Response

class RoomSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='owner.email')
    modified = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S.%f')
    class Meta:
        model = Room
        fields = (
            'name',
            'channel',
            'owner',
            'o365_group',
            'link',
            'modified',
            'geom',
            'centre',
            'extent'
        )
        read_only_fields = ('channel',)

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    authentication_classes =[]

    def create(self, request):
        try:
            http_status = status.HTTP_200_OK
            serializer = RoomSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Check if room exists
            try:
                serializer.instance = Room.objects.get(name=serializer.validated_data['name'])
            except Room.DoesNotExist:
                http_status = status.HTTP_201_CREATED
                
            room = serializer.save()
            
            serializer = RoomSerializer(room)
            return Response(serializer.data, status=http_status)
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError(str(e))
            