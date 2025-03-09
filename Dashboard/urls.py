from django.urls import path,include
from .views import * 

urlpatterns=[
    path('',upload_view,name='index'),
]