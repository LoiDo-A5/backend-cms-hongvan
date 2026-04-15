"""
Discord Webhook notification tasks.
Gửi thông báo lỗi máy in qua Discord Webhook.
"""

import logging
import requests
from celery import shared_task
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

ERROR_CONFIG = {
    'paper_jam':      {'emoji': '🔴', 'label': 'KẸT GIẤY',       'color': 15158332},
    'no_paper':       {'emoji': '🟠', 'label': 'HẾT GIẤY',        'color': 15105570},
    'disconnected':   {'emoji': '🔵', 'label': 'MẤT KẾT NỐI',    'color': 3447003},
    'hardware_error': {'emoji': '🟣', 'label': 'LỖI PHẦN CỨNG',  'color': 10181046},
    'print_failed':   {'emoji': '⚫', 'label': 'IN THẤT BẠI',     'color': 2303786},
}


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_discord_printer_alert(
    self,
    device_id: str,
    error_type: str,
    printer_name: str,
    message: str,
    location: str = None
):
    webhook_url = getattr(settings, 'DISCORD_WEBHOOK_URL', '')
    if not webhook_url:
        logger.warning("[DISCORD] No webhook URL configured, skipping alert")
        return {'status': 'skipped', 'reason': 'no_webhook_url'}

    # Throttle: tránh spam cùng lỗi trong 5 phút
    cache_key = f"discord_alert:{device_id}:{error_type}"
    if cache.get(cache_key):
        logger.info(f"[DISCORD] Throttled alert for {device_id}:{error_type}")
        return {'status': 'throttled'}

    config = ERROR_CONFIG.get(error_type, ERROR_CONFIG['print_failed'])
    location_text = location or "Không xác định"

    mention_role = getattr(settings, 'DISCORD_MENTION_ROLE', '')
    content = mention_role if error_type in ['paper_jam', 'no_paper', 'disconnected'] and mention_role else ""

    payload = {
        "content": content,
        "embeds": [{
            "title": f"{config['emoji']} {config['label']}",
            "color": config['color'],
            "fields": [
                {"name": "🖨️ Máy in",   "value": printer_name or "Unknown",                          "inline": True},
                {"name": "📱 Thiết bị", "value": device_id[:30] if len(device_id) > 30 else device_id, "inline": True},
                {"name": "📍 Vị trí",   "value": location_text,                                        "inline": True},
                {"name": "💬 Chi tiết", "value": (message or "Không có thông tin")[:500],              "inline": False},
            ],
            "footer": {"text": "⏰ Vui lòng kiểm tra ngay!"},
        }]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code in [200, 204]:
            cache.set(cache_key, True, timeout=300)
            logger.info(f"[DISCORD] Alert sent for {device_id}:{error_type}")
            return {'status': 'sent'}
        else:
            logger.error(f"[DISCORD] Failed: {response.status_code} - {response.text}")
            return {'status': 'failed', 'error': response.text}
    except requests.RequestException as e:
        logger.error(f"[DISCORD] Request error: {e}")
        raise self.retry(exc=e)
