from django.urls import path
from .views import (
    UserBasedRecommendationsView,
    MovieBasedRecommendationsView,
    TrendingRecommendationsView,
)

urlpatterns = [
    path("user/", UserBasedRecommendationsView.as_view(), name="user-recommendations"),
    path("movie/<int:movie_id>/", MovieBasedRecommendationsView.as_view(), name="movie-recommendations"),
    path("trending/", TrendingRecommendationsView.as_view(), name="trending-recommendations"),
]
