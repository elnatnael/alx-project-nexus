from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from .views import WelcomeView  # Import the class-based view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

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
    path('', WelcomeView.as_view(), name='welcome'),  # Welcome endpoint

    # Admin
    path('admin/', admin.site.urls),

    # Authentication (Users app + JWT endpoints)
    path('api/auth/', include('users.urls')),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Movies app
    path('api/movies/', include('movies.urls')),

    # Recommendations app
    path('api/recommendations/', include('recommendations.urls')),

    # API Docs
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Debug-only routes
if settings.DEBUG:
    urlpatterns += [
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui-debug'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc-debug'),
    ]
