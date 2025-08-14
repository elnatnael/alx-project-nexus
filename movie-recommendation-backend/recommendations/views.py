from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .recommenders import HybridRecommender
from movies.serializers import MovieSerializer
from movies.models import Movie

class PersonalizedRecommendationsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MovieSerializer

    def get(self, request):
        n = int(request.query_params.get('n', 10))
        
        recommender = HybridRecommender(request.user)
        recommendations = recommender.get_recommendations(n)
        
        # Extract movies from recommendations (which are (movie, score) tuples)
        movies = [rec[0] for rec in recommendations]
        
        serializer = self.get_serializer(movies, many=True)
        return Response({
            'results': serializer.data,
            'algorithm': 'hybrid'
        })

class TrackInteractionView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        movie_id = request.data.get('movie_id')
        interaction_type = request.data.get('interaction_type')
        rating = request.data.get('rating', None)
        
        if not movie_id or not interaction_type:
            return Response(
                {'error': 'movie_id and interaction_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            movie = Movie.objects.get(tmdb_id=movie_id)
        except Movie.DoesNotExist:
            # Fetch movie details from TMDb if not in our DB
            movie_data = fetch_movie_details(movie_id)
            if not movie_data:
                return Response(
                    {'error': 'Movie not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create movie in our DB
            movie = Movie.objects.create(
                tmdb_id=movie_data['id'],
                title=movie_data['title'],
                overview=movie_data['overview'],
                release_date=movie_data['release_date'],
                poster_path=movie_data['poster_path'],
                backdrop_path=movie_data['backdrop_path'],
                popularity=movie_data['popularity'],
                vote_average=movie_data['vote_average'],
                vote_count=movie_data['vote_count']
            )
            
            # Add genres
            for genre_data in movie_data.get('genres', []):
                genre, _ = Genre.objects.get_or_create(
                    tmdb_id=genre_data['id'],
                    defaults={'name': genre_data['name']}
                )
                movie.genres.add(genre)
        
        # Create or update interaction
        interaction, created = UserInteraction.objects.get_or_create(
            user=request.user,
            movie=movie,
            interaction_type=interaction_type,
            defaults={'rating': rating}
        )
        
        if not created and rating is not None:
            interaction.rating = rating
            interaction.save()
        
        return Response(
            {'status': 'success', 'interaction_id': interaction.id},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )