from django.urls import path
from .views import (
    TrendingMoviesView,
    MovieDetailView,
    MovieRecommendationsView,
    SearchMoviesView,
    UserFavoritesView,
    RemoveFavoriteView
)

urlpatterns = [
    path('trending/', TrendingMoviesView.as_view(), name='trending-movies'),
    path('<int:movie_id>/', MovieDetailView.as_view(), name='movie-detail'),
    path('<int:movie_id>/recommendations/', MovieRecommendationsView.as_view(), name='movie-recommendations'),
    path('search/', SearchMoviesView.as_view(), name='search-movies'),
    path('favorites/', UserFavoritesView.as_view(), name='user-favorites'),
    path('favorites/<int:movie_id>/', RemoveFavoriteView.as_view(), name='remove-favorite'),
]