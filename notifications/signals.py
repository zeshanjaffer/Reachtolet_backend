from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import NotificationType
from .inbox_service import create_inbox_notification
from billboards.models import Wishlist, Billboard
import logging

logger = logging.getLogger(__name__)

# Lead/View push + inbox notifications are sent from billboards.tracking (Celery worker),
# not synchronously on post_save — keeps track-view/track-lead APIs fast.

@receiver(post_save, sender=Wishlist)
def send_wishlist_notification(sender, instance, created, **kwargs):
    """Send notification when someone adds a billboard to wishlist"""
    if created and instance.billboard.user:
        try:
            create_inbox_notification(
                user=instance.billboard.user,
                notification_type=NotificationType.WISHLIST_ADDED,
                title="Added to Wishlist! ❤️",
                body=f"Someone added your billboard in {instance.billboard.city} to their wishlist",
                data={
                    'billboard_id': str(instance.billboard.id),
                    'billboard_city': instance.billboard.city,
                    'added_by': instance.user.email if instance.user else 'Anonymous'
                },
                content_object=instance.billboard,
            )
            logger.info(f"Wishlist notification sent to user {instance.billboard.user.id}")
        except Exception as e:
            logger.error(f"Failed to send wishlist notification: {str(e)}")

@receiver(post_save, sender=Billboard)
def send_billboard_status_notification(sender, instance, **kwargs):
    """Send notification when billboard status changes"""
    if not hasattr(instance, '_previous_is_active'):
        return
    if instance.is_active == instance._previous_is_active:
        return
    if not instance.user_id:
        return
    try:
        notification_type = (
            NotificationType.BILLBOARD_ACTIVATED
            if instance.is_active
            else NotificationType.BILLBOARD_DEACTIVATED
        )
        title = "Billboard Activated! ✅" if instance.is_active else "Billboard Deactivated ⏸️"
        body = f"Your billboard in {instance.city} is now {'active' if instance.is_active else 'inactive'}"

        create_inbox_notification(
            user=instance.user,
            notification_type=notification_type,
            title=title,
            body=body,
            data={
                'billboard_id': str(instance.id),
                'billboard_city': instance.city,
                'is_active': instance.is_active,
            },
            content_object=instance,
        )
        logger.info(f"Billboard status notification sent to user {instance.user.id}")
    except Exception as e:
        logger.error(f"Failed to send billboard status notification: {str(e)}")

# Store previous state for comparison — use pre_save so we capture DB state before write
@receiver(pre_save, sender=Billboard)
def store_previous_state(sender, instance, **kwargs):
    """Store the previous state of the billboard for comparison"""
    if instance.pk is None:
        instance._previous_is_active = None
        instance._previous_approval_status = None
        return
    if hasattr(instance, '_previous_is_active') and hasattr(instance, '_previous_approval_status'):
        return
    try:
        previous = Billboard.objects.filter(pk=instance.pk).only(
            'is_active', 'approval_status'
        ).first()
        if previous:
            if not hasattr(instance, '_previous_is_active'):
                instance._previous_is_active = previous.is_active
            if not hasattr(instance, '_previous_approval_status'):
                instance._previous_approval_status = previous.approval_status
        else:
            instance._previous_is_active = None
            instance._previous_approval_status = None
    except Exception:
        instance._previous_is_active = None
        instance._previous_approval_status = None

@receiver(post_save, sender=Billboard)
def send_billboard_approval_notification(sender, instance, **kwargs):
    """Send notification when billboard approval status changes"""
    if not instance.user:
        return
    
    # Check if approval status changed
    if hasattr(instance, '_previous_approval_status'):
        previous_status = instance._previous_approval_status
        current_status = instance.approval_status
        
        # Only send notification if status actually changed
        if previous_status != current_status:
            try:
                if current_status == 'approved':
                    create_inbox_notification(
                        user=instance.user,
                        notification_type=NotificationType.BILLBOARD_APPROVED,
                        title="Billboard Approved! ✅",
                        body=f"Your billboard in {instance.city} has been approved and is now live on the map!",
                        data={
                            'billboard_id': str(instance.id),
                            'billboard_city': instance.city,
                            'approval_status': 'approved',
                            'approved_at': instance.approved_at.isoformat() if instance.approved_at else None
                        },
                        content_object=instance,
                    )
                    logger.info(f"Billboard approval notification sent to user {instance.user.id}")
                    
                elif current_status == 'rejected':
                    rejection_reason = instance.rejection_reason or "No reason provided"
                    create_inbox_notification(
                        user=instance.user,
                        notification_type=NotificationType.BILLBOARD_REJECTED,
                        title="Billboard Rejected ❌",
                        body=f"Your billboard in {instance.city} was rejected. Reason: {rejection_reason}",
                        data={
                            'billboard_id': str(instance.id),
                            'billboard_city': instance.city,
                            'approval_status': 'rejected',
                            'rejection_reason': rejection_reason,
                            'rejected_at': instance.rejected_at.isoformat() if instance.rejected_at else None
                        },
                        content_object=instance,
                    )
                    logger.info(f"Billboard rejection notification sent to user {instance.user.id}")
                    
            except Exception as e:
                logger.error(f"Failed to send approval/rejection notification: {str(e)}")
