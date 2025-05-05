from django.urls import path, include
from .views import *
from django.views.generic import TemplateView

urlpatterns=[
    # Template views
    path('', TemplateView.as_view(template_name="dashboard/index.html"), name='index'),
    path('upload/', upload_view, name='upload'),
    path('datasets/', datasets_view, name='dataset-list-page'),
    path('datasets/<uuid:dataset_id>/', dataset_detail_view, name='dataset-detail-page'),

    # API endpoints
    path('createdataset/', CraeteDatsetView.as_view(), name='create-dataset'),
    path('getdashboard/', GetDashboardView.as_view(), name='get-dashboard'),
    path('getData/', TestDashboardFuctions.as_view(), name='get-dataset'),
    path('aggregations/', DataAggregationView.as_view(), name='data-aggregations'),
    path('dataset-columns/', DatasetColumnAggregationsView.as_view(), name='dataset-column-aggregations'),
    path('api/datasets/', DatasetListView.as_view(), name='dataset-list'),
    path('dataset-status/<uuid:dataset_id>/', DatasetStatusView.as_view(), name='dataset-status'),
    path('api/datasets/<uuid:dataset_id>/', DatasetStatusView.as_view(), name='dataset-detail'),
    path('api/datasets/<uuid:dataset_id>/visualize/', DatasetVisualizationView.as_view(), name='dataset-visualize'),
]