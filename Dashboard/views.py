from django.shortcuts import render
from django.http import JsonResponse
# from requests import Response
from rest_framework.response import Response
from utils.backblaze import upload_file_to_b2, get_file_from_backblaze
from utils.aws_config import upload_file_to_s3
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializer import DatasetCreateSerializer
from Account.models import User
import polars as pl

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
    def post(self,request):
        # breakpoint()
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            
            serializer.save(owner=User.objects.first(),status="READ_PENDING")
            return Response(serializer.data,status=201)
        return Response(data={"error":serializer.errors},status=400)
        
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

        


