from django.urls import path,include
from .views import *

urlpatterns=[
    path('',upload_view,name='index'),
    path('createdataset/',CraeteDatsetView.as_view()),
    path('getdashboard/',GetDashboardView.as_view(),name='get-dashboard'),
    path('getData/',TestDashboardFuctions.as_view(),name='get-dataset'),
    path('aggregations/',DataAggregationView.as_view(),name='data-aggregations'),
    path('dataset-columns/',DatasetColumnAggregationsView.as_view(),name='dataset-column-aggregations'),
]