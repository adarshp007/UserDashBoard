from django.shortcuts import render
from django.http import JsonResponse
# from requests import Response
from rest_framework.response import Response
from rest_framework import status
from utils.aws_config import upload_file_to_s3, upload_dataset_to_s3, get_file_from_s3
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import DatasetCreateSerializer, AggregationRequestSerializer, DatasetSourceSerializer
from Account.models import User, Dataset
import polars as pl
import json
from utils.aggregate import (
    perform_aggregations, get_available_aggregations, get_dataset_column_aggregations,
    get_column_type, perform_axis_based_aggregation
)
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
        file_url = upload_dataset_to_s3(file_path, clean_filename)
        return JsonResponse({"message": "File uploaded!", "url": file_url})

    # For GET requests, render the upload template
    return render(request, 'dashboard/upload.html')

def datasets_view(request):
    """
    View function for the datasets list page.
    """
    return render(request, 'dashboard/datasets.html')

def dataset_detail_view(request, dataset_id):
    """
    View function for the dataset detail page.
    """
    return render(request, 'dashboard/dataset_detail.html')


@method_decorator(csrf_exempt, name='dispatch')
class CraeteDatsetView(APIView):
    permission_classes=[AllowAny]
    serializer_class = DatasetCreateSerializer

    def post(self, request):
        # Create a mutable copy of request.data
        data = request.data.copy()

        # Add the file from request.FILES to the data
        if 'file' in request.FILES:
            data['file'] = request.FILES['file']

        serializer = self.serializer_class(data=data)

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

                # Create a media directory if it doesn't exist
                import os
                media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media', 'uploads')
                os.makedirs(media_dir, exist_ok=True)

                # Use the media directory for temporary file storage
                file_path = os.path.join(media_dir, clean_filename)

                # Save file temporarily
                with open(file_path, "wb") as f:
                    for chunk in file.chunks():
                        f.write(chunk)

                # Log the file path for debugging
                print(f"File saved at: {file_path}")

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
        """
        Get aggregated data from a dataset.
        If a dataset_id is provided, use that dataset.
        Otherwise, use the first available dataset.
        """
        try:
            # Get the dataset ID from the URL parameters
            dataset_id = request.GET.get("dataset_id")

            # If no dataset_id is provided, get the first available dataset
            if not dataset_id:
                datasets = Dataset.objects.filter(status="READ_COMPLETE").order_by('-created_date')
                if not datasets.exists():
                    return Response(
                        {"error": "No datasets available. Please upload a dataset first."},
                        status=status.HTTP_404_NOT_FOUND
                    )
                dataset = datasets.first()
            else:
                # Get the dataset by ID
                dataset = get_object_or_404(Dataset, object_id=dataset_id)

            # Check if the dataset has been processed successfully
            if dataset.status != "READ_COMPLETE" or not dataset.metadata:
                return Response(
                    {"error": f"Dataset is not ready for visualization. Status: {dataset.status}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the file name from the metadata
            if not dataset.metadata or 'file_info' not in dataset.metadata:
                return Response(
                    {"error": "Dataset metadata not found or incomplete"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file_name = dataset.metadata['file_info'].get('filename')
            if not file_name:
                return Response(
                    {"error": "File name not found in dataset metadata"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            print(f"Using file name from dataset {dataset.name}: {file_name}")

            # Get the LazyFrame from S3
            lazy_df = get_file_from_s3(file_name)

            # Convert LazyFrame to DataFrame
            df = lazy_df.collect()

            # Define the aggregations you want to perform
            aggregations = ["mean", "sum", "min", "max"]

            # Perform aggregations for all columns
            data = {
                "dataset_info": {
                    "dataset_id": str(dataset.object_id),
                    "name": dataset.name,
                    "description": dataset.description,
                    "num_rows": df.height,
                    "num_columns": len(df.columns)
                },
                "aggregations": {}
            }

            for column in df.columns:
                # Skip columns with Null data type
                if df.schema[column] != pl.Null:
                    data["aggregations"][column] = {}
                    for agg in aggregations:
                        if agg == "mean":
                            data["aggregations"][column]["mean"] = df[column].mean()
                        elif agg == "sum":
                            data["aggregations"][column]["sum"] = df[column].sum()
                        elif agg == "min":
                            data["aggregations"][column]["min"] = df[column].min()
                        elif agg == "max":
                            data["aggregations"][column]["max"] = df[column].max()

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to get dashboard data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CardDetailsView(APIView):
    def get(self, request):
        # Get the card ID from the URL parameters
        card_id = request.GET.get("id")
        return

class TestDashboardFuctions(APIView):
    permission_classes=[AllowAny]
    def get(self, request):
        """
        Test function to get detailed statistics about a dataset.
        If a dataset_id is provided, use that dataset.
        Otherwise, use the first available dataset.
        """
        try:
            # Get the dataset ID from the URL parameters
            dataset_id = request.GET.get("dataset_id")

            # If no dataset_id is provided, get the first available dataset
            if not dataset_id:
                datasets = Dataset.objects.filter(status="READ_COMPLETE").order_by('-created_date')
                if not datasets.exists():
                    return Response(
                        {"error": "No datasets available. Please upload a dataset first."},
                        status=status.HTTP_404_NOT_FOUND
                    )
                dataset = datasets.first()
            else:
                # Get the dataset by ID
                dataset = get_object_or_404(Dataset, object_id=dataset_id)

            # Check if the dataset has been processed successfully
            if dataset.status != "READ_COMPLETE" or not dataset.metadata:
                return Response(
                    {"error": f"Dataset is not ready for visualization. Status: {dataset.status}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the file name from the metadata
            if not dataset.metadata or 'file_info' not in dataset.metadata:
                return Response(
                    {"error": "Dataset metadata not found or incomplete"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file_name = dataset.metadata['file_info'].get('filename')
            if not file_name:
                return Response(
                    {"error": "File name not found in dataset metadata"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            print(f"Using file name from dataset {dataset.name}: {file_name}")

            # Get the LazyFrame from S3
            lf = get_file_from_s3(file_name)

            # Print the LazyFrame (for debugging)
            print(lf)

            # Get the schema from the LazyFrame
            lf_schema = lf.collect_schema()

            data = {
                "dataset_info": {
                    "dataset_id": str(dataset.object_id),
                    "name": dataset.name,
                    "description": dataset.description,
                    "columns": lf_schema.names(),
                    "column_types": {name: str(dtype) for name, dtype in lf_schema.items()}
                },
                "statistics": {}
            }

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
            # This is the correct way to work with LazyFrames
            stats_df = lf.select(stats_exprs).collect()

            # Convert to nested JSON structure
            for col in lf_schema.keys():
                col_stats = {}
                for stat in ['mean', 'sum', 'min', 'max', 'std', 'unique_count', 'null_count']:
                    stat_name = f"{col}_{stat}"
                    if stat_name in stats_df.columns:
                        col_stats[stat] = stats_df[stat_name][0]
                data["statistics"][col] = col_stats

            return Response(data=data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to get dataset statistics: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
                # Get file name from dataset metadata
                if dataset.metadata and 'file_info' in dataset.metadata:
                    file_name = dataset.metadata['file_info'].get('filename', None)
                else:
                    # Fallback to a default name
                    file_name = f"{dataset.name.replace(' ', '_')}.parquet"
            else:
                # Get dataset by file name
                file_name = validated_data['file_name']

            # Get the LazyFrame
            lazy_df = get_file_from_s3(file_name)

            # Convert to DataFrame for aggregations
            # The perform_aggregations function already handles this conversion,
            # but we're making it explicit here for clarity

            # Perform the aggregations
            aggregation_config = validated_data['aggregations']
            result = perform_aggregations(lazy_df, aggregation_config)

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
                # Get file name from dataset metadata
                if dataset.metadata and 'file_info' in dataset.metadata:
                    file_name = dataset.metadata['file_info'].get('filename', None)
                else:
                    # Fallback to a default name
                    file_name = f"{dataset.name.replace(' ', '_')}.parquet"
            else:
                # Get dataset by file name
                file_name = validated_data['file_name']

            # Get the LazyFrame
            lazy_df = get_file_from_s3(file_name)

            # Convert to DataFrame for aggregations
            # The get_dataset_column_aggregations function already handles this conversion,
            # but we're making it explicit here for clarity

            # Get column aggregations
            result = get_dataset_column_aggregations(lazy_df)

            # Get basic info about the dataset
            # We need to collect the LazyFrame to get this information
            df_info = lazy_df.select(pl.count()).collect()
            num_rows = df_info[0, 0]
            num_columns = len(lazy_df.columns)

            return Response({
                "dataset_info": {
                    "file_name": file_name,
                    "num_columns": num_columns,
                    "num_rows": num_rows
                },
                "columns": result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to get dataset column aggregations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DatasetListView(APIView):
    """
    API view for listing all datasets.

    GET: Get a list of all datasets.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Get a list of all datasets.
        """
        try:
            # Get all datasets, ordered by creation date (newest first)
            datasets = Dataset.objects.all().order_by('-created_date')

            # Prepare the response
            response_data = []
            for dataset in datasets:
                dataset_info = {
                    "dataset_id": str(dataset.object_id),
                    "name": dataset.name,
                    "description": dataset.description,
                    "status": dataset.status,
                    "created_date": dataset.created_date,
                    "modified_date": dataset.modified_date
                }

                # Add basic metadata if available
                if dataset.status == "READ_COMPLETE" and dataset.metadata:
                    if "dataset_info" in dataset.metadata:
                        dataset_info["num_rows"] = dataset.metadata["dataset_info"].get("num_rows", 0)
                        dataset_info["num_columns"] = dataset.metadata["dataset_info"].get("num_columns", 0)

                response_data.append(dataset_info)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to get datasets: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DatasetStatusView(APIView):
    """
    API view for checking the status of a dataset.

    GET: Get the current status and metadata of a dataset.
    DELETE: Delete a dataset.
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

    def delete(self, request, dataset_id=None):
        """
        Delete a dataset.
        """
        try:
            # Get the dataset by ID
            dataset = get_object_or_404(Dataset, object_id=dataset_id)

            # Delete the dataset
            dataset.delete()

            return Response(
                {"message": f"Dataset {dataset_id} deleted successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to delete dataset: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DatasetVisualizationView(APIView):
    """
    API view for generating visualizations from datasets.

    POST: Generate a visualization based on the provided configuration.
    """
    permission_classes = [AllowAny]

    def post(self, request, dataset_id=None):
        """
        Generate a visualization based on the provided configuration.
        """
        try:
            # Get the dataset by ID
            dataset = get_object_or_404(Dataset, object_id=dataset_id)

            # Check if the dataset has been processed successfully
            if dataset.status != "READ_COMPLETE" or not dataset.metadata:
                return Response(
                    {"error": "Dataset is not ready for visualization. Status: " + dataset.status},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the request data
            request_data = request.data

            # Validate required fields
            if 'x_axis' not in request_data or 'y_axis' not in request_data:
                return Response(
                    {"error": "Missing required fields: x_axis and y_axis"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if the dataset has metadata
            if not dataset.metadata:
                return Response(
                    {"error": "Dataset metadata not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the file name from the metadata
            file_name = None
            if 'file_info' in dataset.metadata:
                file_name = dataset.metadata['file_info'].get('filename', None)

            if not file_name:
                # Fallback to a default name
                file_name = f"{dataset.name.replace(' ', '_')}.parquet"

            print(f"Using file name: {file_name}")
            print(f"Dataset metadata: {dataset.metadata}")

            try:
                # Get the LazyFrame from S3
                print(f"Attempting to retrieve file from S3: {file_name}")
                try:
                    lazy_df = get_file_from_s3(file_name)
                    print(f"Successfully retrieved file from S3: {file_name}")

                    # Convert to DataFrame for processing
                    print("Converting LazyFrame to DataFrame...")
                    df = lazy_df.collect()
                    print(f"DataFrame shape: {df.shape}")
                    print(f"DataFrame columns: {df.columns}")
                    print(f"DataFrame first few rows: {df.head(3)}")
                except Exception as e:
                    print(f"Error retrieving or processing file from S3: {str(e)}")
                    raise

                # Extract visualization parameters
                x_axis = request_data['x_axis']
                y_axis = request_data['y_axis']
                chart_type = request_data.get('chart_type', 'bar')

                # Validate that the columns exist in the DataFrame
                print(f"Validating columns: x_axis={x_axis}, y_axis={y_axis}")
                print(f"Available columns in DataFrame: {df.columns}")

                # Check if x_axis exists in the DataFrame
                if isinstance(x_axis, list):
                    for col in x_axis:
                        if col not in df.columns:
                            raise ValueError(f"X-axis column '{col}' not found in dataset. Available columns: {df.columns}")
                elif x_axis not in df.columns:
                    raise ValueError(f"X-axis column '{x_axis}' not found in dataset. Available columns: {df.columns}")

                # Check if y_axis exists in the DataFrame
                if isinstance(y_axis, list):
                    for col in y_axis:
                        if col not in df.columns:
                            raise ValueError(f"Y-axis column '{col}' not found in dataset. Available columns: {df.columns}")
                elif y_axis not in df.columns:
                    raise ValueError(f"Y-axis column '{y_axis}' not found in dataset. Available columns: {df.columns}")

                # Handle x-axis aggregations
                x_axis_aggregations = request_data.get('x_axis_aggregations', {})

                # Handle y-axis aggregations
                y_axis_aggregations = request_data.get('y_axis_aggregations', {})
                print(f"Y-axis aggregations: {y_axis_aggregations}")

                # Handle filter
                filter_column = request_data.get('filter_column', None)
                filter_value = request_data.get('filter_value', None)

                # Apply filter if provided
                if filter_column and filter_value:
                    df = df.filter(pl.col(filter_column) == filter_value)

                # Process the data based on the chart type and aggregations
                # Handle the case where x_axis is a list (should be a single value now)
                if isinstance(x_axis, list) and len(x_axis) > 0:
                    x_axis = x_axis[0]  # Take the first value

                # Use the centralized function to perform aggregations
                print(f"Calling perform_axis_based_aggregation with x_axis={x_axis}, y_axis={y_axis}")
                aggregation_result = perform_axis_based_aggregation(
                    df=df,
                    x_axis=x_axis,
                    y_axis=y_axis,
                    x_axis_aggregations=x_axis_aggregations,
                    y_axis_aggregations=y_axis_aggregations
                )

                # Extract the chart data and metadata
                chart_data = aggregation_result["chart_data"]
                metadata = aggregation_result["metadata"]

                # Debug information
                print(f"Chart labels: {chart_data['labels']}")
                print(f"Chart datasets: {[d['label'] for d in chart_data['datasets']]}")

                # Create summary information
                summary = {
                    "total_rows": len(df),
                    "filtered_rows": len(df) if not filter_column else None,
                    "aggregation_info": f"Aggregation performed using centralized function",
                    "metadata": metadata
                }

                # Return the visualization data
                return Response({
                    "chart_data": chart_data,
                    "summary": summary
                }, status=status.HTTP_200_OK)

            except Exception as e:
                # If there's an error processing the data, return a mock visualization
                # This is for demonstration purposes only
                return Response({
                    "error": f"Error processing data: {str(e)}",
                    "chart_data": self._generate_mock_chart_data(request_data),
                    "is_mock": True
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to generate visualization: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_mock_chart_data(self, request_data):
        """
        Generate mock chart data for demonstration purposes.
        """
        import random

        # Extract visualization parameters
        y_axis = request_data['y_axis']
        chart_type = request_data.get('chart_type', 'bar')

        # Use chart type to adjust the mock data
        is_time_chart = chart_type in ['line', 'area']

        # Generate mock data - use date-like labels if it might be a time series
        if is_time_chart:
            labels = ["2023-01", "2023-02", "2023-03", "2023-04", "2023-05", "2023-06"]
        else:
            labels = ["Category A", "Category B", "Category C", "Category D", "Category E"]
        datasets = []

        # Generate a color palette for the datasets
        colors = [
            {"bg": "rgba(54, 162, 235, 0.5)", "border": "rgba(54, 162, 235, 1)"},
            {"bg": "rgba(255, 99, 132, 0.5)", "border": "rgba(255, 99, 132, 1)"},
            {"bg": "rgba(255, 206, 86, 0.5)", "border": "rgba(255, 206, 86, 1)"},
            {"bg": "rgba(75, 192, 192, 0.5)", "border": "rgba(75, 192, 192, 1)"},
            {"bg": "rgba(153, 102, 255, 0.5)", "border": "rgba(153, 102, 255, 1)"},
            {"bg": "rgba(255, 159, 64, 0.5)", "border": "rgba(255, 159, 64, 1)"},
            {"bg": "rgba(201, 203, 207, 0.5)", "border": "rgba(201, 203, 207, 1)"}
        ]

        # Check if y_axis is a list or a single value
        y_axes = y_axis if isinstance(y_axis, list) else [y_axis]

        # Create a dataset for each y-axis variable
        for i, y_var in enumerate(y_axes):
            datasets.append({
                "label": y_var,
                "data": [random.randint(10, 100) for _ in range(len(labels))],
                "backgroundColor": colors[i % len(colors)]["bg"],
                "borderColor": colors[i % len(colors)]["border"],
                "borderWidth": 1
            })

        return {
            "labels": labels,
            "datasets": datasets
        }
