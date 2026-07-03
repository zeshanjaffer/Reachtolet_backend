import logging

from celery import shared_task

from .tracking import record_billboard_lead, record_billboard_view

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10, ignore_result=True)
def track_billboard_view_task(self, billboard_id, user_id=None, user_ip=None, user_agent=''):
    try:
        result = record_billboard_view(
            billboard_id=billboard_id,
            user_id=user_id,
            user_ip=user_ip,
            user_agent=user_agent or '',
        )
        logger.info('track_billboard_view_task billboard=%s result=%s', billboard_id, result)
        return result
    except Exception as exc:
        logger.exception('track_billboard_view_task failed billboard=%s', billboard_id)
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=10, ignore_result=True)
def track_billboard_lead_task(self, billboard_id, user_id=None, user_ip=None, user_agent=''):
    try:
        result = record_billboard_lead(
            billboard_id=billboard_id,
            user_id=user_id,
            user_ip=user_ip,
            user_agent=user_agent or '',
        )
        logger.info('track_billboard_lead_task billboard=%s result=%s', billboard_id, result)
        return result
    except Exception as exc:
        logger.exception('track_billboard_lead_task failed billboard=%s', billboard_id)
        raise self.retry(exc=exc) from exc
