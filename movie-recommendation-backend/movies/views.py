import json
from django.core.cache import cache
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Movie, Genre, UserFavorite
from .serializers import MovieSerializer, UserFavoriteSerializer, TMDBSerializer
from .tmdb import fetch_trending_movies, fetch_movie_details, fetch_recommendations, search_movies
from core.decorators import cache_response_method

class TrendingMoviesView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get trending movies from TMDb API",
        manual_parameters=[
            openapi.Parameter(
                'time_window',
                openapi.IN_QUERY,
                description="Time window for trending movies (day/week)",
                type=openapi.TYPE_STRING,
                default='week',
                enum=['day', 'week']
            )
        ],
        responses={
            200: openapi.Response('Successful response', TMDBSerializer(many=True)),
            401: openapi.Response('Unauthorized'),
            500: openapi.Response('Internal Server Error')
        },
        security=[{'Bearer': []}]
    )
    @cache_response_method(timeout=21600)  # 6 hours
    def get(self, request):
        time_window = request.query_params.get('time_window', 'week')
        movies = fetch_trending_movies(time_window)
        
        if movies is None:
            return Response({'error': 'Failed to fetch trending movies'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = TMDBSerializer(data=movies, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.data)

class MovieDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get detailed information about a specific movie",
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                additional_properties=True
            )),
            401: openapi.Response('Unauthorized'),
            404: openapi.Response('Movie not found'),
            500: openapi.Response('Internal Server Error')
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, movie_id):
        cache_key = f'movie_details_{movie_id}'
        
        # Try to get data from cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(json.loads(cached_data))
        
        # Fetch from TMDb if not in cache
        movie_details = fetch_movie_details(movie_id)
        if movie_details is None:
            return Response({'error': 'Failed to fetch movie details'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Cache the data for 24 hours
        cache.set(cache_key, json.dumps(movie_details), timeout=86400)
        
        return Response(movie_details)

class MovieRecommendationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get recommendations based on a specific movie",
        responses={
            200: openapi.Response('Successful response', TMDBSerializer(many=True)),
            401: openapi.Response('Unauthorized'),
            404: openapi.Response('Movie not found'),
            500: openapi.Response('Internal Server Error')
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, movie_id):
        cache_key = f'movie_recommendations_{movie_id}'
        
        # Try to get data from cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(json.loads(cached_data))
        
        # Fetch from TMDb if not in cache
        recommendations = fetch_recommendations(movie_id)
        if recommendations is None:
            return Response({'error': 'Failed to fetch recommendations'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Validate and serialize data
        serializer = TMDBSerializer(data=recommendations, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Cache the data for 12 hours
        cache.set(cache_key, json.dumps(serializer.data), timeout=43200)
        
        return Response(serializer.data)

class SearchMoviesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Search movies by title",
        manual_parameters=[
            openapi.Parameter(
                'query',
                openapi.IN_QUERY,
                description="Search query string",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response('Successful response', TMDBSerializer(many=True)),
            400: openapi.Response('Bad Request - Query parameter missing'),
            401: openapi.Response('Unauthorized'),
            500: openapi.Response('Internal Server Error')
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        query = request.query_params.get('query', '')
        if not query:
            return Response({'error': 'Query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        cache_key = f'movie_search_{query.lower()}'
        
        # Try to get data from cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(json.loads(cached_data))
        
        # Fetch from TMDb if not in cache
        results = search_movies(query)
        if results is None:
            return Response({'error': 'Failed to search movies'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Validate and serialize data
        serializer = TMDBSerializer(data=results, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Cache the data for 1 hour
        cache.set(cache_key, json.dumps(serializer.data), timeout=3600)
        
        return Response(serializer.data)

class UserFavoritesView(generics.ListCreateAPIView):
    serializer_class = UserFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all favorite movies for the current user",
        responses={
            200: openapi.Response('Successful response', UserFavoriteSerializer(many=True)),
            401: openapi.Response('Unauthorized')
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Add a movie to user's favorites",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['movie_id'],
            properties={
                'movie_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='TMDb movie ID')
            }
        ),
        responses={
            201: openapi.Response('Successfully created', UserFavoriteSerializer),
            400: openapi.Response('Bad Request - Invalid movie ID'),
            401: openapi.Response('Unauthorized'),
            500: openapi.Response('Internal Server Error')
        },
        security=[{'Bearer': []}]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return UserFavorite.objects.filter(user=self.request.user).select_related('movie')

    def perform_create(self, serializer):
        movie_id = self.request.data.get('movie_id')
        movie_data = fetch_movie_details(movie_id)
        
        if not movie_data:
            raise serializers.ValidationError({'movie_id': 'Invalid movie ID'})
        
        # Get or create genres
        genres = []
        for genre_data in movie_data.get('genres', []):
            genre, _ = Genre.objects.get_or_create(
                tmdb_id=genre_data['id'],
                defaults={'name': genre_data['name']}
            )
            genres.append(genre)
        
        # Get or create movie
        movie, _ = Movie.objects.get_or_create(
            tmdb_id=movie_data['id'],
            defaults={
                'title': movie_data['title'],
                'overview': movie_data['overview'],
                'release_date': movie_data['release_date'],
                'poster_path': movie_data['poster_path'],
                'backdrop_path': movie_data['backdrop_path'],
                'popularity': movie_data['popularity'],
                'vote_average': movie_data['vote_average'],
                'vote_count': movie_data['vote_count'],
            }
        )
        movie.genres.set(genres)
        
        # Create favorite
        serializer.save(user=self.request.user, movie=movie)

class RemoveFavoriteView(generics.DestroyAPIView):
    queryset = UserFavorite.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Remove a movie from user's favorites",
        responses={
            204: openapi.Response('Successfully deleted'),
            401: openapi.Response('Unauthorized'),
            404: openapi.Response('Favorite not found')
        },
        security=[{'Bearer': []}]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_object(self):
        movie_id = self.kwargs.get('movie_id')
        return generics.get_object_or_404(
            UserFavorite,
            user=self.request.user,
            movie__tmdb_id=movie_id
        )