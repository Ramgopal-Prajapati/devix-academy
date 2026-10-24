from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import public_home
from accounts.views import CustomLoginView, custom_logout_view, permission_denied_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public Home
    path('', public_home, name='public_home'),

    # Direct Auth Shortcuts
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', custom_logout_view, name='logout'),

    # App URLs
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('branch-head/', include('academy.urls_branch_head', namespace='branch_head')),
    path('trainer/', include('academy.urls_trainer', namespace='trainer')),
    path('student/', include('academy.urls_student', namespace='student')),

    # REST APIs
    path('api/', include('devix_academy.api_urls')),
]

# Media and Static files serving during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Custom error handlers
handler403 = 'accounts.views.permission_denied_view'
