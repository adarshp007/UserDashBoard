from Account.models import Dataset
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

class DatasetCreateSerializer(ModelSerializer):
    file = serializers.FileField(required=True)

    class Meta:
        model = Dataset
        fields = ['name', 'description', 'file']
