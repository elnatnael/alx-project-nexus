from django.urls import path
from .views import PersonalizedRecommendationsView, TrackInteractionView

urlpatterns = [
    path('personalized/', PersonalizedRecommendationsView.as_view(), name='personalized-recommendations'),
    path('interactions/', TrackInteractionView.as_view(), name='track-interaction'),
]