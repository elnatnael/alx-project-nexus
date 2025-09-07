import json
from django.core.cache import cache
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from movies.models import UserFavorite
from movies.serializers import TMDBSerializer
from movies.tmdb import fetch_recommendations, fetch_movie_details, fetch_trending_movies


class UserBasedRecommendationsView(APIView):
    """
    Generate recommendations for the logged-in user
    based on their favorite movies.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get personalized recommendations for the current user",
        responses={
            200: openapi.Response("Successful response", TMDBSerializer(many=True)),
            401: openapi.Response("Unauthorized"),
            500: openapi.Response("Internal Server Error"),
        },
    )
    def get(self, request):
        user = request.user
        cache_key = f"user_recommendations_{user.id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        favorites = UserFavorite.objects.filter(user=user).select_related("movie")
        if not favorites.exists():
            return Response(
                {"message": "No favorites found for this user"},
                status=status.HTTP_200_OK,
            )

        # For simplicity, pick the first favorite movie and get recommendations
        first_fav = favorites.first().movie
        recommendations = fetch_recommendations(first_fav.tmdb_id)

        if recommendations is None:
            return Response(
                {"error": "Failed to fetch recommendations"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = TMDBSerializer(data=recommendations, many=True)
        if serializer.is_valid():
            cache.set(cache_key, serializer.data, timeout=21600)  # 6 hours
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MovieBasedRecommendationsView(APIView):
    """
    Generate recommendations based on a given movie ID.
    Public endpoint (no auth required).
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Get recommendations for a specific movie",
        responses={
            200: openapi.Response("Successful response", TMDBSerializer(many=True)),
            404: openapi.Response("Movie not found"),
            500: openapi.Response("Internal Server Error"),
        },
    )
    def get(self, request, movie_id):
        cache_key = f"movie_recommendations_{movie_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        # Ensure movie exists
        movie = fetch_movie_details(movie_id)
        if movie is None:
            return Response(
                {"error": "Movie not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        recommendations = fetch_recommendations(movie_id)
        if recommendations is None:
            return Response(
                {"error": "Failed to fetch recommendations"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = TMDBSerializer(data=recommendations, many=True)
        if serializer.is_valid():
            cache.set(cache_key, serializer.data, timeout=21600)  # 6 hours
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrendingRecommendationsView(APIView):
    """
    Fetch trending movies as a form of recommendations.
    Public endpoint (no auth required).
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Get trending movies (as recommendations)",
        responses={
            200: openapi.Response("Successful response", TMDBSerializer(many=True)),
            500: openapi.Response("Internal Server Error"),
        },
    )
    def get(self, request):
        cache_key = "trending_recommendations"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        trending = fetch_trending_movies(time_window="week")
        if trending is None:
            return Response(
                {"error": "Failed to fetch trending movies"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = TMDBSerializer(data=trending, many=True)
        if serializer.is_valid():
            cache.set(cache_key, serializer.data, timeout=21600)  # 6 hours
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
