from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from .views import profile, submit_reads, user_settings
from .views import CustomLoginView, CustomSignupView, picture, loading
from .views import change_password
from .views import download_file, delete_file, batch_action_results
from .views import results, view_file

urlpatterns = [
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    path('accounts/profile_picture', picture, name='picture'),
    path('accounts/loading', loading, name='loading'),
    path('accounts/home/', profile, name='home'),
    path('accounts/submit/', submit_reads, name='submit'),
    path('accounts/results/', results, name='results'),
    path('accounts/results/<path:folder_path>', results, name='results_with_path'),
    path('view_file/<str:file_type>/<str:filename>/', view_file, name='view_file'),
    path('accounts/settings', user_settings, name='settings'),
    path('accounts/password/reset', change_password, name='update'),
    path('download_file/', download_file, name='download_file'),
    path('delete_file/', delete_file, name='delete_file'),
    path('accounts/batch_action_results', batch_action_results, name='batch_action_results'),
    path('accounts/', include('allauth.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
