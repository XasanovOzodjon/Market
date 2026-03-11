from rest_framework import serializers


class GetUIDSerializer(serializers.Serializer):
    unicID = serializers.CharField(max_length=255)
    