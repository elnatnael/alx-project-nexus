from rest_framework import serializers
from .models import Movie, Genre, UserFavorite

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'tmdb_id', 'name']

class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True)
    
    class Meta:
        model = Movie
        fields = ['id', 'tmdb_id', 'title', 'overview', 'release_date', 
                 'poster_path', 'backdrop_path', 'popularity', 
                 'vote_average', 'vote_count', 'genres']

class UserFavoriteSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()
    
    class Meta:
        model = UserFavorite
        fields = ['id', 'movie', 'created_at']

class TMDBSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(required=False, allow_blank=True)
    original_title = serializers.CharField(required=False, allow_blank=True)
    overview = serializers.CharField(required=False, allow_blank=True)
    release_date = serializers.CharField(required=False, allow_blank=True)
    poster_path = serializers.CharField(required=False, allow_null=True)
    backdrop_path = serializers.CharField(required=False, allow_null=True)
    popularity = serializers.FloatField(required=False)
    vote_average = serializers.FloatField(required=False)
    vote_count = serializers.IntegerField(required=False)
    genre_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )

    def get_title(self, obj):
        return obj.get('title') or obj.get('original_title')
