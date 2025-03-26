from Account.models import Dataset
from rest_framework.serializers import ModelSerializer

class DatasetCreateSerializer(ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['name', 'description', 'file']
