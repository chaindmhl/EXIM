from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import api_views

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Simple test endpoint
    path('test/', api_views.mobile_test, name='mobile_test'),

    # Student dashboard redirect
    path('dashboard/', api_views.api_dashboard_redirect, name='mobile_dashboard'),

    # Upload exam answer
    path('exam/upload/', api_views.api_upload_answer, name='mobile_upload_answer'),

    # Practice endpoints
    path('practice/start/', api_views.api_get_practice_exam, name='mobile_practice_start'),
    path('practice/submit/', api_views.api_submit_practice, name='mobile_practice_submit'),

    # Analytics dashboard
    path('analytics/', api_views.api_analytics_dashboard, name='mobile_analytics'),
]