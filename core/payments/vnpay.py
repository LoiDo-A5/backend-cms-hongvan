"""
Ký và kiểm tra HMAC SHA512 theo hướng dẫn VNPAY PAY (v2.1.0).
"""
from __future__ import annotations

import hashlib
import hmac
from typing import Any
from urllib.parse import quote_plus, urlencode


def build_hmac_sign_data(params: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in sorted(params.keys()):
        if key in ('vnp_SecureHash', 'vnp_SecureHashType'):
            continue
        val = params[key]
        if val is None or str(val) == '':
            continue
        parts.append(f'{key}={val}')
    return '&'.join(parts)


def hmac_sha512_hex(secret: str, sign_data: str) -> str:
    return hmac.new(
        secret.encode('utf-8'),
        sign_data.encode('utf-8'),
        hashlib.sha512,
    ).hexdigest()


def build_payment_secure_hash(params: dict[str, Any], hash_secret: str) -> str:
    sign_data = build_hmac_sign_data(params)
    return hmac_sha512_hex(hash_secret, sign_data)


def verify_callback_secure_hash(
    params: dict[str, Any],
    hash_secret: str,
    secure_hash: str | None,
) -> bool:
    if not secure_hash:
        return False
    expected = build_payment_secure_hash(params, hash_secret)
    return hmac.compare_digest(expected.lower(), secure_hash.lower())


def build_payment_url(base_url: str, params: dict[str, Any]) -> str:
    ordered = sorted(params.items(), key=lambda x: x[0])
    qs = urlencode(ordered, quote_via=quote_plus)
    sep = '&' if '?' in base_url else '?'
    return f'{base_url}{sep}{qs}'


def normalize_order_info_ascii(text: str, max_len: int = 255) -> str:
    import unicodedata

    s = unicodedata.normalize('NFKD', text)
    out = ''.join(c for c in s if not unicodedata.combining(c))
    out = out.replace('\n', ' ').strip()
    if len(out) > max_len:
        out = out[: max_len - 3] + '...'
    return out or 'Payment'
