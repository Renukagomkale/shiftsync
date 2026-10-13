from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", views.MeView.as_view()),
    path("business/", views.BusinessView.as_view()),
    path("business/join/", views.JoinBusinessView.as_view()),
    path("business/members/", views.MembersView.as_view()),
]
