"""
Đăng ký URL webhook lên VietQR.IO (API confirmWebhook).

Bước B trong luồng: server bạn gọi VietQR để báo "khi có CK, POST về URL này".

Chạy::

    python manage.py vietqr_register_webhook https://your-domain.com/api/payments/vietqr/webhook/

Cần trong .env.local::

    VIETQR_CLIENT_ID=...
    VIETQR_API_KEY=...

Lấy Client ID / API Key từ https://my.vietqr.io (tài liệu: x-client-id, x-api-key).

Luu y: POST https://api.vietqr.io/v2/paymentGateway/confirmWebhook co the tra 404
("Endpoint not found") neu VietQR doi gateway — khi do dang ky webhook bang giao dien
my.vietqr.io hoac Casso (developer.casso.vn), khong qua lenh nay.

API (khi con hoat dong): POST https://api.vietqr.io/v2/paymentGateway/confirmWebhook
"""
from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand

VIETQR_CONFIRM_WEBHOOK_API = 'https://api.vietqr.io/v2/paymentGateway/confirmWebhook'


class Command(BaseCommand):
    help = 'Gọi VietQR confirmWebhook để đăng ký webhook_url (x-client-id + x-api-key).'

    def add_arguments(self, parser):
        parser.add_argument(
            'webhook_url',
            nargs='?',
            type=str,
            help='URL HTTPS công khai, ví dụ https://domain.com/api/payments/vietqr/webhook/',
        )

    def handle(self, *args, **options):
        client_id = (getattr(settings, 'VIETQR_CLIENT_ID', None) or '').strip()
        api_key = (getattr(settings, 'VIETQR_API_KEY', None) or '').strip()
        if not client_id or not api_key:
            self.stderr.write(
                self.style.ERROR(
                    'Thiếu VIETQR_CLIENT_ID hoặc VIETQR_API_KEY trong .env (my.vietqr.io).'
                )
            )
            return

        raw = (options.get('webhook_url') or '').strip()
        if not raw:
            self.stderr.write(
                self.style.ERROR(
                    'Thiếu tham số: python manage.py vietqr_register_webhook '
                    'https://<domain>/api/payments/vietqr/webhook/'
                )
            )
            return

        if not raw.startswith('https://'):
            self.stderr.write(
                self.style.WARNING('Nên dùng URL HTTPS (VietQR yêu cầu URL công khai).')
            )

        body = json.dumps({'webhook_url': raw}).encode('utf-8')
        req = urllib.request.Request(
            VIETQR_CONFIRM_WEBHOOK_API,
            data=body,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'x-client-id': client_id,
                'x-api-key': api_key,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as resp:
                text = resp.read().decode('utf-8', errors='replace')
                self.stdout.write(f'HTTP {resp.status}\n{text}')
                if resp.status == 200:
                    try:
                        data = json.loads(text)
                        if data.get('code') == '00':
                            self.stdout.write(self.style.SUCCESS('Đăng ký webhook thành công.'))
                        else:
                            self.stdout.write(self.style.WARNING(f'Phản hồi: {data}'))
                    except json.JSONDecodeError:
                        pass
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='replace') if e.fp else ''
            self.stderr.write(self.style.ERROR(f'HTTP {e.code}: {err_body or e.reason}'))
            if e.code == 404:
                self.stdout.write(
                    self.style.WARNING(
                        '\nNeu la "Endpoint not found": endpoint api.vietqr.io co the da doi. '
                        'Hay dang ky Webhook URL tren my.vietqr.io (hoac Casso: '
                        'https://developer.casso.vn ) thu cong, tro toi:\n'
                        '  POST https://<domain>/api/payments/vietqr/webhook/\n'
                        'Webhook khong lien quan toi localhost:5173 (chi can HTTPS cong khai).'
                    )
                )
        except urllib.error.URLError as e:
            self.stderr.write(self.style.ERROR(str(e)))
