"""
Tạo link thanh toán: ``POST https://api.vietqr.io/v2/paymentRequests`` (tài liệu PDF) — không chữ ký.

Tùy chọn override URL: ``VIETQR_LEGACY_PAYMENT_URL``.
"""
from __future__ import annotations

import json
import logging
import ssl
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_PAYMENT_URL = 'https://api.vietqr.io/v2/paymentRequests'


class VietQrApiError(Exception):
    """Lỗi HTTP hoặc phản hồi không hợp lệ từ API tạo link."""

    def __init__(self, message: str, *, status: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status = status
        self.body = body


def _payment_request_url() -> str:
    full = (getattr(settings, 'VIETQR_LEGACY_PAYMENT_URL', None) or '').strip()
    if full:
        return full
    return DEFAULT_PAYMENT_URL


def post_payment_request(payload: dict[str, Any]) -> dict[str, Any]:
    """
    POST tạo link. Header: ``x-client-id``, ``x-api-key``.
    Payload: orderCode, amount, description, template, items, cancelUrl, successUrl (PDF).
    """
    client_id = (getattr(settings, 'VIETQR_CLIENT_ID', None) or '').strip()
    api_key = (getattr(settings, 'VIETQR_API_KEY', None) or '').strip()
    if not client_id or not api_key:
        raise VietQrApiError('Thiếu VIETQR_CLIENT_ID hoặc VIETQR_API_KEY trong cấu hình.')

    url = _payment_request_url()
    label = 'api.vietqr.io'

    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        method='POST',
        headers={
            'Content-Type': 'application/json; charset=utf-8',
            'x-client-id': client_id,
            'x-api-key': api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45, context=ssl.create_default_context()) as resp:
            text = resp.read().decode('utf-8', errors='replace')
            data = json.loads(text)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace') if e.fp else ''
        logger.warning('%s paymentRequests HTTP %s: %s', label, e.code, err_body[:500])
        raise VietQrApiError(
            f'{label} trả lỗi HTTP {e.code}',
            status=e.code,
            body=err_body,
        ) from e
    except urllib.error.URLError as e:
        logger.warning('%s paymentRequests network: %s', label, e)
        raise VietQrApiError(f'Không kết nối được máy chủ thanh toán ({label}): {e}') from e
    except json.JSONDecodeError as e:
        raise VietQrApiError('Phản hồi không phải JSON hợp lệ.') from e

    return data
