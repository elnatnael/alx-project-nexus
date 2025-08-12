# alx-project-nexus
🎬 Movie Recommendation Backend - ProDev BE

    A robust backend system for a movie recommendation app that mirrors real-world backend development scenarios with a focus on performance, security, and API usability.

🚀 Overview

    This backend powers a movie recommendation application by providing:
    🔐 Secure user authentication (JWT)
    🎞️ Movie recommendation APIs (via TMDb)
    ❤️ Favorite movie management
    ⚡ High-performance caching (Redis)
    📄 Public API documentation (Swagger)
🎯 Project Goals

    API Development: Endpoints for trending & recommended movies
    User Management: Signup, login, and favorite movie features
    Performance Optimization: Redis caching for faster response times
    Documentation: Swagger UI for API testing and frontend use
🛠️ Tech Stack
   
    Backend: Django
    Database: PostgreSQL
    Caching: Redis
    API Docs: Swagger (drf-yasg)
    External API: TMDb (The Movie Database)
✨ Key Features
    
    Movie Recommendations:
    Fetches trending and recommended movies using TMDb API with error handling.
    User Authentication & Preferences:
    JWT-based auth with endpoints for saving and retrieving favorite movies.
    Performance Optimization:
    Redis caching for external API responses to reduce latency and load.
    API Documentation:
    Publicly accessible at: /api/docs/
