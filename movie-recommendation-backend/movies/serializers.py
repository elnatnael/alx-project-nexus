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
    title = serializers.CharField()
    overview = serializers.CharField()
    release_date = serializers.CharField(required=False)
    poster_path = serializers.CharField(allow_null=True)
    backdrop_path = serializers.CharField(allow_null=True)
    popularity = serializers.FloatField()
    vote_average = serializers.FloatField()
    vote_count = serializers.IntegerField()
    genre_ids = serializers.ListField(child=serializers.IntegerField(), required=False)