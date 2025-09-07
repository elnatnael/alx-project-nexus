from django.urls import path
from .views import (
    TrendingMoviesView,
    MovieDetailView,
    MovieRecommendationsView,
    SearchMoviesView,
    UserFavoritesView,
    RemoveFavoriteView,
    MovieListView,
    TopRatedMoviesView, 
    UpcomingMoviesView  # ✅ add here
)

urlpatterns = [
    path('', MovieListView.as_view(), name='movie-list'),
    path('trending/', TrendingMoviesView.as_view(), name='trending-movies'),
    path('top-rated/', TopRatedMoviesView.as_view(), name='top-rated-movies'),  # ✅ new
    path('upcoming/', UpcomingMoviesView.as_view(), name='upcoming-movies'),
    path('<int:movie_id>/', MovieDetailView.as_view(), name='movie-detail'),
    path('<int:movie_id>/recommendations/', MovieRecommendationsView.as_view(), name='movie-recommendations'),
    path('search/', SearchMoviesView.as_view(), name='search-movies'),
    path('favorites/', UserFavoritesView.as_view(), name='user-favorites'),
    path('favorites/<int:movie_id>/', RemoveFavoriteView.as_view(), name='remove-favorite'),
]
