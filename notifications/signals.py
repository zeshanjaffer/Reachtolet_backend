from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import NotificationType
from .services import push_service
from billboards.models import Lead, View, Wishlist, Billboard
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Lead)
def send_lead_notification(sender, instance, created, **kwargs):
    """Send notification when a new lead is created"""
    if created and instance.billboard.user:
        try:
            # Send notification to billboard owner
            push_service.send_notification(
                user=instance.billboard.user,
                notification_type=NotificationType.NEW_LEAD,
                title="New Lead! 🎉",
                body=f"Someone showed interest in your billboard in {instance.billboard.city}",
                data={
                    'billboard_id': str(instance.billboard.id),
                    'billboard_city': instance.billboard.city,
                    'lead_count': instance.billboard.leads
                },
                content_object=instance.billboard
            )
            logger.info(f"Lead notification sent to user {instance.billboard.user.id}")
        except Exception as e:
            logger.error(f"Failed to send lead notification: {str(e)}")

@receiver(post_save, sender=View)
def send_view_notification(sender, instance, created, **kwargs):
    """Send notification when a new view is created (optional, can be rate limited)"""
    if created and instance.billboard.user:
        try:
            # Only send view notifications for significant milestones (e.g., every 10 views)
            if instance.billboard.views % 10 == 0 and instance.billboard.views > 0:
                push_service.send_notification(
                    user=instance.billboard.user,
                    notification_type=NotificationType.NEW_VIEW,
                    title="Views Milestone! 👀",
                    body=f"Your billboard in {instance.billboard.city} reached {instance.billboard.views} views!",
                    data={
                        'billboard_id': str(instance.billboard.id),
                        'billboard_city': instance.billboard.city,
                        'view_count': instance.billboard.views
                    },
                    content_object=instance.billboard
                )
                logger.info(f"View milestone notification sent to user {instance.billboard.user.id}")
        except Exception as e:
            logger.error(f"Failed to send view notification: {str(e)}")

@receiver(post_save, sender=Wishlist)
def send_wishlist_notification(sender, instance, created, **kwargs):
    """Send notification when someone adds a billboard to wishlist"""
    if created and instance.billboard.user:
        try:
            push_service.send_notification(
                user=instance.billboard.user,
                notification_type=NotificationType.WISHLIST_ADDED,
                title="Added to Wishlist! ❤️",
                body=f"Someone added your billboard in {instance.billboard.city} to their wishlist",
                data={
                    'billboard_id': str(instance.billboard.id),
                    'billboard_city': instance.billboard.city,
                    'added_by': instance.user.email if instance.user else 'Anonymous'
                },
                content_object=instance.billboard
            )
            logger.info(f"Wishlist notification sent to user {instance.billboard.user.id}")
        except Exception as e:
            logger.error(f"Failed to send wishlist notification: {str(e)}")

@receiver(post_save, sender=Billboard)
def send_billboard_status_notification(sender, instance, **kwargs):
    """Send notification when billboard status changes"""
    if hasattr(instance, '_previous_is_active'):
        # Status changed
        if instance.is_active != instance._previous_is_active:
            try:
                notification_type = NotificationType.BILLBOARD_ACTIVATED if instance.is_active else NotificationType.BILLBOARD_DEACTIVATED
                title = "Billboard Activated! ✅" if instance.is_active else "Billboard Deactivated ⏸️"
                body = f"Your billboard in {instance.city} is now {'active' if instance.is_active else 'inactive'}"
                
                push_service.send_notification(
                    user=instance.user,
                    notification_type=notification_type,
                    title=title,
                    body=body,
                    data={
                        'billboard_id': str(instance.id),
                        'billboard_city': instance.city,
                        'is_active': instance.is_active
                    },
                    content_object=instance
                )
                logger.info(f"Billboard status notification sent to user {instance.user.id}")
            except Exception as e:
                logger.error(f"Failed to send billboard status notification: {str(e)}")

# Store previous state for comparison
@receiver(post_save, sender=Billboard)
def store_previous_state(sender, instance, **kwargs):
    """Store the previous state of the billboard for comparison"""
    if not hasattr(instance, '_previous_is_active'):
        try:
            # Get the previous state from database
            previous = Billboard.objects.get(id=instance.id)
            instance._previous_is_active = previous.is_active
            instance._previous_approval_status = previous.approval_status
        except Billboard.DoesNotExist:
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
                    # Billboard was approved
                    push_service.send_notification(
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
                        content_object=instance
                    )
                    logger.info(f"Billboard approval notification sent to user {instance.user.id}")
                    
                elif current_status == 'rejected':
                    # Billboard was rejected
                    rejection_reason = instance.rejection_reason or "No reason provided"
                    push_service.send_notification(
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
                        content_object=instance
                    )
                    logger.info(f"Billboard rejection notification sent to user {instance.user.id}")
                    
            except Exception as e:
                logger.error(f"Failed to send approval/rejection notification: {str(e)}")
