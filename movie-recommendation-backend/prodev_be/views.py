from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class WelcomeView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'Welcome to Movie Recommendation API',
            'endpoints': {
                'admin/':'admin.site.urls',
                'api_docs': '/api/docs/',
                'admin': '/admin/',
                'api_auth': '/api/auth/',
                'api_movies': '/api/movies/',
                'api_recommendations': '/api/recommendations/'
            }
        })