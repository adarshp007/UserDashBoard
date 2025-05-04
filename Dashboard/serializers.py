from rest_framework import serializers
from Account.models import Dataset

class DatasetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['name', 'description', 'file']

class AggregationRequestSerializer(serializers.Serializer):
    """
    Serializer for validating aggregation requests.
    """
    dataset_id = serializers.UUIDField(required=False, help_text="UUID of the dataset to aggregate")
    file_name = serializers.CharField(required=False, help_text="Name of the file to aggregate")
    aggregations = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        help_text="Dictionary mapping column names to lists of aggregation functions"
    )

    def validate(self, data):
        """
        Validate that either dataset_id or file_name is provided, but not both.
        """
        if 'dataset_id' not in data and 'file_name' not in data:
            raise serializers.ValidationError("Either dataset_id or file_name must be provided")

        if 'dataset_id' in data and 'file_name' in data:
            raise serializers.ValidationError("Only one of dataset_id or file_name should be provided")

        return data

class DatasetSourceSerializer(serializers.Serializer):
    """
    Serializer for validating dataset source requests.
    """
    dataset_id = serializers.UUIDField(required=False, help_text="UUID of the dataset to analyze")
    file_name = serializers.CharField(required=False, help_text="Name of the file to analyze")

    def validate(self, data):
        """
        Validate that either dataset_id or file_name is provided, but not both.
        """
        if 'dataset_id' not in data and 'file_name' not in data:
            raise serializers.ValidationError("Either dataset_id or file_name must be provided")

        if 'dataset_id' in data and 'file_name' in data:
            raise serializers.ValidationError("Only one of dataset_id or file_name should be provided")

        return data
