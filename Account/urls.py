from rest_framework_simplejwt.views import TokenRefreshView

from django.urls import path

from . import views

app_name = "account"

urlpatterns = [
    # Web views
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # API endpoints
    path("api/login/", views.LoginAPIView.as_view(), name="api_login"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/user/", views.UserDetailAPIView.as_view(), name="user_detail"),
]
