from django.shortcuts import render
from django.http import JsonResponse
# from requests import Response
from rest_framework.response import Response
from rest_framework import status
from utils.backblaze import upload_file_to_b2, get_file_from_backblaze
from utils.aws_config import upload_file_to_s3
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import DatasetCreateSerializer, AggregationRequestSerializer, DatasetSourceSerializer
from Account.models import User, Dataset
import polars as pl
from utils.aggregate import perform_aggregations, get_available_aggregations, get_dataset_column_aggregations
from django.shortcuts import get_object_or_404
from .tasks import process_dataset_file

# Create your views here.
@csrf_exempt
def upload_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        # Trim whitespace and replace spaces with underscores
        clean_filename = "_".join(file.name.strip().split())
        file_path = f"/tmp/{clean_filename}"
        # Save file temporarily
        with open(file_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
        file_url = upload_file_to_b2(file_path, clean_filename)
        return JsonResponse({"message": "File uploaded!", "url": file_url})
    return JsonResponse({"error": "Invalid request"}, status=400)
class CraeteDatsetView(APIView):
    permission_classes=[AllowAny]
    serializer_class = DatasetCreateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            try:
                # Get the uploaded file
                file = request.FILES.get("file")
                if not file:
                    return Response(
                        {"error": "No file was uploaded"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Trim whitespace and replace spaces with underscores
                clean_filename = "_".join(file.name.strip().split())
                file_path = f"/tmp/{clean_filename}"

                # Save file temporarily
                with open(file_path, "wb") as f:
                    for chunk in file.chunks():
                        f.write(chunk)

                # Create dataset with initial status
                dataset = serializer.save(
                    owner=User.objects.first(),
                    status="READ_PENDING"
                )

                # Launch Celery task to process the file in the background
                process_dataset_file.delay(file_path, clean_filename, str(dataset.object_id))

                # Return immediate response
                return Response({
                    "message": "Dataset creation initiated. Processing in background.",
                    "dataset": serializer.data,
                    "dataset_id": str(dataset.object_id),
                    "status": "READ_PENDING",
                    "note": "Metadata and aggregation possibilities will be available once processing is complete."
                }, status=status.HTTP_202_ACCEPTED)

            except Exception as e:
                return Response(
                    {"error": f"Failed to initiate dataset processing: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # def post(self, request):
    #     # Get the uploaded file from the request
    #     file = request.FILES.get("file")
    #     user_email = "adarsh.p@beinex.com"
    #     # Trim whitespace and replace spaces with underscores
    #     clean_filename = "_".join(file.name.strip().split())
    #     file_path = f"/tmp/{clean_filename}"
    #     # Save file temporarily
    #     with open(file_path, "wb") as f:
    #         for chunk in file.chunks():
    #             f.write(chunk)
    #     file_url = upload_file_to_s3(file_path,clean_filename,user_email)
    #     return JsonResponse({"success": "Upload success fully"}, status=200)

class CreateDashboardView(APIView):
    def post(self, request):
        # Get the dashboard data from the request body
        dashboard_data = request.data
        return
class GetDashboardView(APIView):
    permission_classes=[AllowAny]
    def get(self, request):
        # Get the dashboard ID from the URL parameters
        # dashboard_id = request.GET.get("id")
        file_name="Employment_to_population_ratio_for_residents_in_the_Emirate_of_Abu_Dhabi_by_region_and_gender_-_quarterly.csv_(2).xlsx"
        df=get_file_from_backblaze(file_name)
        # To convert records to dictionary
        # data=df.to_dicts()
        # Define the aggregations you want to perform
        aggregations = ["mean", "sum", "min", "max"]
        # Perform aggregations for all columns
        data = {}
        for column in df.columns:
            # Skip columns with Null data type
            if df.schema[column] != pl.Null:
                data[column] = {}
                for agg in aggregations:
                    if agg == "mean":
                        data[column]["mean"] = df[column].mean()
                    elif agg == "sum":
                        data[column]["sum"] = df[column].sum()
                    elif agg == "min":
                        data[column]["min"] = df[column].min()
                    elif agg == "max":
                        data[column]["max"] = df[column].max()
        return Response(data,status=200)

class CardDetailsView(APIView):
    def get(self, request):
        # Get the card ID from the URL parameters
        card_id = request.GET.get("id")
        return

class TestDashboardFuctions(APIView):
    permission_classes=[AllowAny]
    def get(self, request):
        # Get the dashboard ID from the URL parameters
        dashboard_id = request.GET.get("id")
        # dashboard_id = 1
        file_name="Employment_to_population_ratio_for_residents_in_the_Emirate_of_Abu_Dhabi_by_region_and_gender_-_quarterly.csv_(2).xlsx"
        # breakpoint()
        lf=get_file_from_backblaze(file_name)
        # To convert records to dictionary
        print(lf)
        lf_schema=lf.collect_schema()
        columns=lf_schema.names()
        dtype=lf_schema.dtypes()

        data={}
        # data["columns"]=columns
        # data["datatypes"]=dtype
        # Prepare statistics expressions
        stats_exprs = []
        for name, dtype in lf_schema.items():
            if dtype in (pl.Int64, pl.Int32, pl.Float64, pl.Float32):
                stats_exprs.extend([
                    pl.col(name).mean().round(2).alias(f"{name}_mean"),
                    pl.col(name).sum().alias(f"{name}_sum"),
                    pl.col(name).min().alias(f"{name}_min"),
                    pl.col(name).max().alias(f"{name}_max"),
                    pl.col(name).std().alias(f"{name}_std")  # Bonus: standard deviation
                ])
            elif dtype == pl.Utf8:
                stats_exprs.extend([
                    pl.col(name).n_unique().alias(f"{name}_unique_count"),
                    pl.col(name).first().alias(f"{name}_first_sample"),
                    pl.col(name).len().alias(f"{name}_count")
                ])
            elif dtype == pl.Null:
                stats_exprs.append(
                    pl.col(name).is_null().sum().alias(f"{name}_null_count")
                )

        # Execute the query and collect results
        stats_df = lf.select(stats_exprs).collect()
        # Convert to nested JSON structure
        result = {}
        for col in lf_schema.keys():
            col_stats = {}
            for stat in ['mean', 'sum', 'min', 'max', 'std', 'unique_count', 'null_count']:
                stat_name = f"{col}_{stat}"
                if stat_name in stats_df.columns:
                    col_stats[stat] = stats_df[stat_name][0]
            data[col] = col_stats

        return Response(data=data,status=200)


class DataAggregationView(APIView):
    """
    API view for performing aggregations on datasets.

    POST: Perform aggregations on a dataset based on the provided configuration.
    GET: Get information about available aggregation functions.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Get information about available aggregation functions.
        """
        return Response({
            "available_aggregations": get_available_aggregations(),
            "usage_example": {
                "dataset_id": "uuid-of-dataset",  # or "file_name": "filename.xlsx"
                "aggregations": {
                    "column1": ["mean", "sum", "min", "max"],
                    "column2": ["unique_count", "most_frequent"]
                }
            }
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Perform aggregations on a dataset based on the provided configuration.
        """
        serializer = AggregationRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        try:
            # Get the dataset based on the provided identifier
            if 'dataset_id' in validated_data:
                # Get dataset by ID
                dataset = get_object_or_404(Dataset, object_id=validated_data['dataset_id'])
                # TODO: Implement logic to get the file from the dataset
                # For now, we'll use a placeholder
                file_name = "Employment_to_population_ratio_for_residents_in_the_Emirate_of_Abu_Dhabi_by_region_and_gender_-_quarterly.csv_(2).xlsx"
            else:
                # Get dataset by file name
                file_name = validated_data['file_name']

            # Get the dataframe
            df = get_file_from_backblaze(file_name)

            # Perform the aggregations
            aggregation_config = validated_data['aggregations']
            result = perform_aggregations(df, aggregation_config)

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to perform aggregations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DatasetColumnAggregationsView(APIView):
    """
    API view for getting available aggregations for each column in a dataset.

    POST: Get available aggregations for each column in a dataset based on its data type.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Get available aggregations for each column in a dataset based on its data type.
        """
        serializer = DatasetSourceSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        try:
            # Get the dataset based on the provided identifier
            if 'dataset_id' in validated_data:
                # Get dataset by ID
                dataset = get_object_or_404(Dataset, object_id=validated_data['dataset_id'])
                # TODO: Implement logic to get the file from the dataset
                # For now, we'll use a placeholder
                file_name = "Employment_to_population_ratio_for_residents_in_the_Emirate_of_Abu_Dhabi_by_region_and_gender_-_quarterly.csv_(2).xlsx"
            else:
                # Get dataset by file name
                file_name = validated_data['file_name']

            # Get the dataframe
            df = get_file_from_backblaze(file_name)

            # Get column aggregations
            result = get_dataset_column_aggregations(df)

            return Response({
                "dataset_info": {
                    "file_name": file_name,
                    "num_columns": len(df.columns),
                    "num_rows": df.height
                },
                "columns": result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to get dataset column aggregations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DatasetStatusView(APIView):
    """
    API view for checking the status of a dataset.

    GET: Get the current status and metadata of a dataset.
    """
    permission_classes = [AllowAny]

    def get(self, request, dataset_id=None):
        """
        Get the current status and metadata of a dataset.
        """
        try:
            # Get the dataset by ID
            dataset = get_object_or_404(Dataset, object_id=dataset_id)

            # Prepare the response based on the dataset status
            response_data = {
                "dataset_id": str(dataset.object_id),
                "name": dataset.name,
                "description": dataset.description,
                "status": dataset.status,
                "created_date": dataset.created_date,
                "modified_date": dataset.modified_date
            }

            # If the dataset has been processed successfully, include metadata
            if dataset.status == "READ_COMPLETE" and dataset.metadata:
                response_data["dataset_info"] = dataset.metadata.get("dataset_info", {})
                response_data["columns"] = dataset.metadata.get("columns", {})

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to get dataset status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
