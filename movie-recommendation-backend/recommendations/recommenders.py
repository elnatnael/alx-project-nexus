from django.db.models import Count, Avg
from movies.models import Movie
from users.models import User
from recommendations.models import UserInteraction, Recommendation
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
from django.db import models


class BaseRecommender:
    def __init__(self, user):
        self.user = user
    
    def get_recommendations(self, n=10):
        raise NotImplementedError
        
    def save_recommendations(self, recommendations, algorithm_name):
        # Clear old recommendations for this algorithm
        Recommendation.objects.filter(user=self.user, algorithm=algorithm_name).delete()
        
        # Save new recommendations
        for movie, score in recommendations:
            Recommendation.objects.create(
                user=self.user,
                movie=movie,
                score=score,
                algorithm=algorithm_name
            )
    
    def get_user_interactions(self):
        return UserInteraction.objects.filter(user=self.user)
    
    def get_user_favorites(self):
        return self.get_user_interactions().filter(interaction_type='FAV')
    
    def get_user_rated_movies(self):
        return self.get_user_interactions().filter(interaction_type='RATE').exclude(rating__isnull=True)
    
    def get_user_viewed_movies(self):
        return self.get_user_interactions().filter(interaction_type='VIEW')

class PopularityRecommender(BaseRecommender):
    def get_recommendations(self, n=10):
        # Get most popular movies not interacted with by the user
        interacted_movie_ids = self.get_user_interactions().values_list('movie_id', flat=True)
        
        # Calculate popularity score based on views, favorites, and average rating
        popular_movies = Movie.objects.exclude(id__in=interacted_movie_ids).annotate(
            view_count=Count('userinteraction__id', filter=models.Q(userinteraction__interaction_type='VIEW')),
            fav_count=Count('userinteraction__id', filter=models.Q(userinteraction__interaction_type='FAV')),
            avg_rating=Avg('userinteraction__rating', filter=models.Q(userinteraction__interaction_type='RATE'))
        ).order_by('-view_count', '-fav_count', '-avg_rating', '-popularity')[:n]
        
        # Normalize scores between 0 and 1
        max_view = max(m.view_count for m in popular_movies) if popular_movies else 1
        max_fav = max(m.fav_count for m in popular_movies) if popular_movies else 1
        max_rating = max(m.avg_rating for m in popular_movies) if popular_movies else 5
        
        recommendations = []
        for movie in popular_movies:
            view_score = movie.view_count / max_view if max_view > 0 else 0
            fav_score = movie.fav_count / max_fav if max_fav > 0 else 0
            rating_score = movie.avg_rating / max_rating if movie.avg_rating else 0
            total_score = 0.3 * view_score + 0.4 * fav_score + 0.3 * rating_score
            recommendations.append((movie, total_score))
        
        # Sort by total score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        self.save_recommendations(recommendations, 'popularity')
        return recommendations

class ContentBasedRecommender(BaseRecommender):
    def get_recommendations(self, n=10):
        # Get user's favorite and highly rated movies
        user_favorites = self.get_user_favorites().values_list('movie_id', flat=True)
        user_rated = self.get_user_rated_movies().filter(rating__gte=3.5).values_list('movie_id', flat=True)
        seed_movie_ids = list(user_favorites) + list(user_rated)
        
        if not seed_movie_ids:
            return []
        
        # Get all movies not interacted with by the user
        interacted_movie_ids = self.get_user_interactions().values_list('movie_id', flat=True)
        candidate_movies = Movie.objects.exclude(id__in=interacted_movie_ids)
        
        if not candidate_movies:
            return []
        
        # Prepare data for TF-IDF
        seed_movies = Movie.objects.filter(id__in=seed_movie_ids)
        all_movies = list(seed_movies) + list(candidate_movies)
        
        # Create document for each movie: title + overview + genres
        documents = []
        for movie in all_movies:
            genres = " ".join([genre.name for genre in movie.genres.all()])
            doc = f"{movie.title} {movie.overview} {genres}"
            documents.append(doc)
        
        # Compute TF-IDF features
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        # Compute cosine similarity between seed movies and all candidates
        seed_count = len(seed_movies)
        similarity_matrix = cosine_similarity(tfidf_matrix[:seed_count], tfidf_matrix[seed_count:])
        
        # Average similarity across all seed movies
        avg_similarity = similarity_matrix.mean(axis=0)
        
        # Get top N recommendations
        top_indices = avg_similarity.argsort()[::-1][:n]
        recommendations = []
        for idx in top_indices:
            movie = candidate_movies[idx]
            score = float(avg_similarity[idx])
            recommendations.append((movie, score))
        
        self.save_recommendations(recommendations, 'content-based')
        return recommendations

class HybridRecommender(BaseRecommender):
    def get_recommendations(self, n=10):
        # Get recommendations from different algorithms
        popularity_rec = PopularityRecommender(self.user).get_recommendations(n * 2)
        content_rec = ContentBasedRecommender(self.user).get_recommendations(n * 2)
        
        # Combine and deduplicate
        all_rec = {}
        for movie, score in popularity_rec:
            all_rec[movie.id] = (movie, score * 0.4)  # Weight for popularity
        
        for movie, score in content_rec:
            if movie.id in all_rec:
                # If movie is in both, average with higher weight to content-based
                existing_movie, existing_score = all_rec[movie.id]
                all_rec[movie.id] = (movie, (existing_score * 0.4 + score * 0.6))
            else:
                all_rec[movie.id] = (movie, score * 0.6)
        
        # Sort by combined score
        recommendations = sorted(all_rec.values(), key=lambda x: x[1], reverse=True)[:n]
        
        self.save_recommendations(recommendations, 'hybrid')
        return recommendations