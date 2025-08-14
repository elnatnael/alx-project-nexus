from django.db import models
from users.models import User
from movies.models import Movie

class UserInteraction(models.Model):
    INTERACTION_TYPES = [
        ('VIEW', 'View'),
        ('RATE', 'Rate'),
        ('FAV', 'Favorite'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=4, choices=INTERACTION_TYPES)
    rating = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['movie', 'interaction_type']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.movie.title} - {self.get_interaction_type_display()}"

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    score = models.FloatField()
    algorithm = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie', 'algorithm')

    def __str__(self):
        return f"{self.user.username} - {self.movie.title} - {self.algorithm} ({self.score})"