from django.urls import path, include
from . import views
from .views import (
    PackageDownloadView, RegisterView, CustomLoginView,
    PackageListAPIView, PackageDetailAPIView, PackageVersionDetailAPIView,
    PackageDownloadAPIView, PackageDetailView, PackageUploadView,
    PackageUpdateView, PackageVerificationView, MyPackagesView,
    PackageDeleteView
)
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers  
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.package_list, name='main'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='main'), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('my-packages/', MyPackagesView.as_view(), name='my-packages'),
    path('package/<str:pkg_name>/delete/', 
         PackageDeleteView.as_view(), 
         name='delete-package'),
    path('download/<str:pkg_name>/<str:pkg_version>/',
         PackageDownloadView.as_view(), 
         name='download-package'),
    path('api/packages/', PackageListAPIView.as_view(), name='package-list'),
    path('api/packages/<str:pkg_name>/', PackageDetailAPIView.as_view(), name='package-detail'),
    path('api/packages/<str:pkg_name>/versions/<str:pkg_version>/',
         PackageVersionDetailAPIView.as_view(),
         name='package-version-detail'),
    path('api/packages/<str:pkg_name>/download/<str:pkg_version>/',
         PackageDownloadAPIView.as_view(),
         name='package-download'),
    path('package/<str:pkg_name>/', PackageDetailView.as_view(), name='package-detail-view'),
    path('upload/', PackageUploadView.as_view(), name='upload-package'),
    path('package/<slug:pkg_name>/update/', 
         PackageUpdateView.as_view(), 
         name='update-package'),
    path('package/<str:pkg_name>/<str:pkg_version>/verify/',
         PackageVerificationView.as_view(),
         name='verify-package'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
