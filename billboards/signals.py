"""
Django signals for billboard model to handle cache invalidation.
Ensures cached map data is refreshed when billboards are created/updated/deleted.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Billboard
import logging

logger = logging.getLogger(__name__)

# Cache version key - increments when billboards change
CACHE_VERSION_KEY = 'billboards_cache_version'

def get_cache_version():
    """Get current cache version number"""
    return cache.get(CACHE_VERSION_KEY, 1)

def increment_cache_version():
    """Increment cache version to invalidate all cached billboard map data"""
    current_version = cache.get(CACHE_VERSION_KEY, 1)
    new_version = current_version + 1
    cache.set(CACHE_VERSION_KEY, new_version, timeout=None)  # Never expires
    logger.info(f"Billboard cache version incremented to {new_version}")
    return new_version

@receiver(post_save, sender=Billboard)
def invalidate_billboard_cache_on_save(sender, instance, **kwargs):
    """
    Invalidate billboard map cache when a billboard is created or updated.
    This ensures users see new/updated billboards within 2 minutes (cache TTL).
    """
    # Only invalidate if approval_status or is_active changed (affects map visibility)
    if hasattr(instance, '_previous_approval_status'):
        if instance._previous_approval_status != instance.approval_status:
            increment_cache_version()
            logger.info(f"Cache invalidated: Billboard {instance.id} approval_status changed")
    elif instance.approval_status == 'approved' and instance.is_active:
        # New approved billboard - invalidate cache
        increment_cache_version()
        logger.info(f"Cache invalidated: New approved billboard {instance.id}")

@receiver(post_delete, sender=Billboard)
def invalidate_billboard_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when a billboard is deleted"""
    increment_cache_version()
    logger.info(f"Cache invalidated: Billboard {instance.id} deleted")

