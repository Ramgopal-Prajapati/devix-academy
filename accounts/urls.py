from django.urls import path
from .views import (
    CustomLoginView, custom_logout_view,
    role_redirect_view, CustomPasswordChangeView
)

app_name = 'accounts'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('redirect/', role_redirect_view, name='role_redirect'),
    path('change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
]
