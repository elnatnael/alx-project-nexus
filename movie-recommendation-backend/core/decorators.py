from django.core.cache import cache
from functools import wraps
import json
from django.utils.decorators import method_decorator

def cache_response(timeout):
    """
    Custom decorator to cache API responses
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            cache_key = f"view_{request.path}_{request.META['QUERY_STRING']}"
            cached_data = cache.get(cache_key)
            
            if cached_data is not None:
                return json.loads(cached_data)
                
            response = func(request, *args, **kwargs)
            if response.status_code == 200:
                cache.set(cache_key, json.dumps(response.data), timeout=timeout)
            return response
        return wrapper
    return decorator

def cache_response_method(timeout):
    """
    Method decorator version for class-based views
    """
    def decorator(method):
        @wraps(method)
        def wrapper(obj, request, *args, **kwargs):
            cache_key = f"method_{request.path}_{request.META['QUERY_STRING']}"
            cached_data = cache.get(cache_key)
            
            if cached_data is not None:
                return json.loads(cached_data)
                
            response = method(obj, request, *args, **kwargs)
            if response.status_code == 200:
                cache.set(cache_key, json.dumps(response.data), timeout=timeout)
            return response
        return wrapper
    return decorator