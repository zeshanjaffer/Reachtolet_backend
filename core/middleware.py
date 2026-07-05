"""
Middleware to close old database connections and prevent connection pool exhaustion.
"""
from django.db import connections
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class CloseOldConnectionsMiddleware(MiddlewareMixin):
    """
    Close old database connections after each request to prevent connection pool exhaustion.
    This is especially important for Supabase free tier which has limited connections.
    """
    
    def process_response(self, request, response):
        """Close DB connections after each request (critical for Supabase session pooler)."""
        for conn in connections.all():
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")
        return response

    def process_exception(self, request, exception):
        """Close connections even if there's an exception"""
        for conn in connections.all():
            try:
                conn.close()
            except Exception:
                pass
        return None

