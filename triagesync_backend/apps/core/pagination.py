"""
Shared pagination classes for consistent pagination across the application.
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for list endpoints.
    
    Default page size: 20
    Max page size: 100
    Query params: page, page_size
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
