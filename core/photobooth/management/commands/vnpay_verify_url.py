"""
Parse URL thanh toán VNPAY đầy đủ (copy từ response payment_url), tính lại hash và so khớp với vnp_SecureHash.

Chạy (trong Docker):
  docker compose exec app python manage.py vnpay_verify_url "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?..."

- Match: True → chuỗi ký + secret trong container khớp URL.
- Match: False → secret khác, URL bị sửa, hoặc tham số parse sai.

Không dùng URL trang lỗi (Payment/Error.html?code=70) — cần URL vpcpay.html có đủ query và vnp_SecureHash.
"""
from __future__ import annotations

import urllib.parse

from django.conf import settings
from django.core.management.base import BaseCommand

from core.photobooth.vnpay import build_hmac_sign_data, build_payment_secure_hash


class Command(BaseCommand):
    help = 'So khớp vnp_SecureHash trên URL với hash tính lại từ secret trong settings.'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='Payment URL đầy đủ (copy từ JSON payment_url)')

    def handle(self, *args, **options):
        raw = options['url'].strip()
        if not raw.startswith('http'):
            self.stdout.write(self.style.ERROR('URL không hợp lệ.'))
            return

        parsed = urllib.parse.urlparse(raw)
        qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)
        flat: dict[str, str] = {}
        for k, v in qs.items():
            if v:
                flat[k] = v[-1]

        got = flat.pop('vnp_SecureHash', None)
        flat.pop('vnp_SecureHashType', None)

        if not got:
            self.stdout.write(self.style.ERROR('Thiếu vnp_SecureHash trên URL (cần URL vpcpay, không phải trang Error).'))
            return

        hex_ok = len(got) == 128 and all(c in '0123456789abcdefABCDEF' for c in got)
        if not hex_ok:
            self.stdout.write(
                self.style.ERROR(
                    'vnp_SecureHash không đúng định dạng (cần 128 ký tự hex). '
                    'Bạn có thể đang dán URL mẫu có "..." — hãy copy nguyên payment_url từ JSON API, không rút gọn.'
                )
            )
            self.stdout.write(self.style.WARNING(f'Giá trị hiện tại (len={len(got)}): {got!r}'))
            return

        if any('...' in (flat.get(k) or '') for k in flat):
            self.stdout.write(
                self.style.ERROR(
                    'Tham số URL chứa "..." — đó là placeholder, không phải dữ liệu thật. '
                    'Copy toàn bộ payment_url từ response POST /api/payments/vnpay/create/.'
                )
            )
            return

        sec = getattr(settings, 'VNPAY_HASH_SECRET', '') or ''
        expected = build_payment_secure_hash(flat, sec)
        sign_data = build_hmac_sign_data(flat)

        match = expected.lower() == got.lower()
        self.stdout.write(f'vnp_SecureHash trên URL: {got[:32]}... (len={len(got)})')
        self.stdout.write(f'Hash tính lại local:  {expected[:32]}... (len={len(expected)})')
        self.stdout.write(self.style.SUCCESS('Match: True') if match else self.style.ERROR('Match: False'))
        self.stdout.write('')
        self.stdout.write('sign_data (len=%d):' % len(sign_data))
        self.stdout.write(sign_data)
