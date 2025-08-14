from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from .views import WelcomeView  # Import the class-based view

# Schema view for Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Movie Recommendation API",
        default_version='v1',
        description="API for the Movie Recommendation App",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@movierecommendation.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('', WelcomeView.as_view(), name='welcome'),  # Use as_view() for class-based view
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/movies/', include('movies.urls')),
    path('api/recommendations/', include('recommendations.urls')),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += [
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui-debug'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc-debug'),
    ]