import json
from django.core.cache import cache
from rest_framework import generics, status, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Movie, Genre, UserFavorite
from .serializers import MovieSerializer, UserFavoriteSerializer, TMDBSerializer
from .tmdb import fetch_trending_movies, fetch_movie_details, fetch_recommendations, search_movies, fetch_top_rated, fetch_upcoming

class TopRatedMoviesView(APIView):
    """
    Get top-rated movies (cached for 6 hours).
    Public endpoint (no authentication required).
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Get top-rated movies from TMDB (cached for 6 hours)",
        responses={
            200: openapi.Response("Successful response", TMDBSerializer(many=True)),
            500: "Internal Server Error",
        },
    )
    def get(self, request):
        cache_key = "top_rated_movies"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        movies = fetch_top_rated()  # Call TMDB API
        if movies is None:
            return Response(
                {"error": "Failed to fetch top-rated movies"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = TMDBSerializer(data=movies, many=True)
        if serializer.is_valid():
            cache.set(cache_key, serializer.data, timeout=21600)  # 6 hours
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrendingMoviesView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Get trending movies from TMDb API",
        manual_parameters=[
            openapi.Parameter(
                "time_window",
                openapi.IN_QUERY,
                description="Time window for trending movies (day/week)",
                type=openapi.TYPE_STRING,
                default="week",
                enum=["day", "week"],
            )
        ],
        responses={
            200: openapi.Response("Successful response", TMDBSerializer(many=True)),
            401: openapi.Response("Unauthorized"),
            500: openapi.Response("Internal Server Error"),
        },
    )
    def get(self, request):
        time_window = request.query_params.get("time_window", "week")
        cache_key = f"trending_movies_{time_window}"

        # Check cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            tmdb_response = fetch_trending_movies(time_window)
            if tmdb_response is None:
                return Response(
                    {"error": "Failed to fetch trending movies from TMDB"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            movies = tmdb_response.get("results", []) if isinstance(tmdb_response, dict) else tmdb_response
            if not isinstance(movies, list):
                return Response(
                    {"error": "Invalid data format from TMDB API"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            serializer = TMDBSerializer(data=movies, many=True)
            if not serializer.is_valid():
                return Response(
                    {"error": "Data validation failed", "details": serializer.errors},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            cache.set(cache_key, serializer.data, timeout=21600)  # 6 hours
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Unexpected error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MovieDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get detailed information about a specific movie",
        responses={
            200: openapi.Response(
                "Successful response",
                openapi.Schema(type=openapi.TYPE_OBJECT, additional_properties=True),
            ),
            401: openapi.Response("Unauthorized"),
            404: openapi.Response("Movie not found"),
            500: openapi.Response("Internal Server Error"),
        },
    )
    def get(self, request, movie_id):
        cache_key = f"movie_details_{movie_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        movie_details = fetch_movie_details(movie_id)
        if movie_details is None:
            return Response(
                {"error": "Failed to fetch movie details"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        cache.set(cache_key, movie_details, timeout=86400)  # 24 hours
        return Response(movie_details, status=status.HTTP_200_OK)


class MovieRecommendationsView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Get recommendations based on a specific movie",
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

        recommendations = fetch_recommendations(movie_id)
        if recommendations is None:
            return Response(
                {"error": "Failed to fetch recommendations"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = TMDBSerializer(data=recommendations, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cache.set(cache_key, serializer.data, timeout=43200)  # 12 hours
        return Response(serializer.data, status=status.HTTP_200_OK)


class SearchMoviesView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Search movies by title",
        manual_parameters=[
            openapi.Parameter(
                "query",
                openapi.IN_QUERY,
                description="Search query string",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={
            200: openapi.Response("Successful response", TMDBSerializer(many=True)),
            400: openapi.Response("Bad Request - Query parameter missing"),
            500: openapi.Response("Internal Server Error"),
        },
    )
    def get(self, request):
        query = request.query_params.get("query", "")
        if not query:
            return Response(
                {"error": "Query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache_key = f"movie_search_{query.lower()}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        results = search_movies(query)
        if results is None:
            return Response(
                {"error": "Failed to search movies"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = TMDBSerializer(data=results, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cache.set(cache_key, serializer.data, timeout=3600)  # 1 hour
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserFavoritesView(generics.ListCreateAPIView):
    serializer_class = UserFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserFavorite.objects.filter(user=self.request.user).select_related("movie")

    def perform_create(self, serializer):
        movie_id = self.request.data.get("movie_id")
        movie_data = fetch_movie_details(movie_id)

        if not movie_data:
            raise serializers.ValidationError({"movie_id": "Invalid movie ID"})

        genres = []
        for genre_data in movie_data.get("genres", []):
            genre, _ = Genre.objects.get_or_create(
                tmdb_id=genre_data["id"], defaults={"name": genre_data["name"]}
            )
            genres.append(genre)

        movie, _ = Movie.objects.get_or_create(
            tmdb_id=movie_data.get("id"),
            defaults={
                "title": movie_data.get("title") or movie_data.get("original_title", ""),
                "overview": movie_data.get("overview", ""),
                "release_date": movie_data.get("release_date"),
                "poster_path": movie_data.get("poster_path"),
                "backdrop_path": movie_data.get("backdrop_path"),
                "popularity": movie_data.get("popularity", 0.0),
                "vote_average": movie_data.get("vote_average", 0.0),
                "vote_count": movie_data.get("vote_count", 0),
            },
        )
        movie.genres.set(genres)
        serializer.save(user=self.request.user, movie=movie)


class RemoveFavoriteView(generics.DestroyAPIView):
    queryset = UserFavorite.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        movie_id = self.kwargs.get("movie_id")
        return generics.get_object_or_404(
            UserFavorite, user=self.request.user, movie__tmdb_id=movie_id
        )


class MovieListView(generics.ListAPIView):
    queryset = Movie.objects.all().prefetch_related("genres")
    serializer_class = MovieSerializer
    permission_classes = [permissions.IsAuthenticated]


class UpcomingMoviesView(APIView):
    """
    Get upcoming movies (public endpoint).
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Get upcoming movies",
        responses={200: openapi.Response("Success", TMDBSerializer(many=True))}
    )
    def get(self, request):
        cache_key = "upcoming_movies"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        movies = fetch_upcoming()
        if movies is None:
            return Response(
                {"error": "Failed to fetch upcoming movies"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = TMDBSerializer(data=movies, many=True)
        if serializer.is_valid():
            cache.set(cache_key, serializer.data, timeout=21600)  # 6 hours
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




