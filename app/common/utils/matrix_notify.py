"""
Matrix notification utility — gửi tin nhắn vào room Element/Matrix.

Cấu hình (trong .env):
    MATRIX_HOMESERVER=https://chat.hongvan.net
    MATRIX_BOT_TOKEN=syt_...
    MATRIX_ROOM_ID=!KXZDFNxHdttqXgYBZp:hongvan.net

Đặc điểm:
- Gửi bất đồng bộ (thread riêng, không block request).
- Cooldown 5 phút/device/lỗi để tránh spam khi lỗi lặp lại liên tục.
- txnId = f"{device_id_short}-{error_key}-{unix_ms}" — đảm bảo unique.
"""
from __future__ import annotations

import logging
import time
import threading
import urllib.request
import urllib.error
import json
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# ── Cooldown registry (in-memory) ────────────────────────────────────────────
# key = f"{device_id}:{error_key}", value = last_sent_timestamp (float)
_cooldown: dict[str, float] = {}
_cooldown_lock = threading.Lock()
COOLDOWN_SECONDS = 5 * 60  # 5 phút giữa 2 lần cùng loại lỗi cùng máy

# ── Error type → tiếng Việt ───────────────────────────────────────────────────
ERROR_LABELS: dict[str, str] = {
    "paper_jam":        "🔴 Kẹt giấy",
    "no_paper":         "🟡 Hết giấy",
    "low_paper":        "🟡 Sắp hết giấy",
    "no_ink":           "🟡 Hết mực",
    "low_ink":          "🟡 Sắp hết mực",
    "disconnected":     "🔴 Mất kết nối máy in",
    "offline":          "🔴 Máy in offline",
    "hardware_error":   "🔴 Lỗi phần cứng máy in",
    "print_failed":     "🔴 In thất bại",
    "cover_open":       "🟡 Nắp máy in đang mở",
    "error":            "🔴 Máy in gặp lỗi",
}


def _send_sync(device_name: str, error_key: str, detail: str, printer_name: str) -> None:
    """Chạy trong thread riêng — gửi PUT lên Matrix homeserver."""
    homeserver = getattr(settings, "MATRIX_HOMESERVER", "").rstrip("/")
    token = getattr(settings, "MATRIX_BOT_TOKEN", "")
    room_id = getattr(settings, "MATRIX_ROOM_ID", "")

    if not homeserver or not token or not room_id:
        logger.warning("[MATRIX] Chưa cấu hình MATRIX_HOMESERVER / MATRIX_BOT_TOKEN / MATRIX_ROOM_ID")
        return

    label = ERROR_LABELS.get(error_key, f"⚠️ {error_key}")
    body_lines = [
        f"📷 *Ward Alert*",
        f"Máy: *{device_name}*",
        f"Lỗi: *{label}*",
    ]
    if printer_name and printer_name != "Unknown":
        body_lines.append(f"Máy in: {printer_name}")
    if detail:
        body_lines.append(f"Chi tiết: {detail}")

    message_body = "\n".join(body_lines)
    txn_id = f"{device_name[:20].replace(' ', '_')}-{error_key}-{int(time.time() * 1000)}"

    import urllib.parse
    encoded_room = urllib.parse.quote(room_id, safe="")
    encoded_txn = urllib.parse.quote(txn_id, safe="")
    url = f"{homeserver}/_matrix/client/v3/rooms/{encoded_room}/send/m.room.message/{encoded_txn}"

    payload = json.dumps({"msgtype": "m.text", "body": message_body}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="PUT",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info(f"[MATRIX] Gửi thành công: {resp.status} — {device_name} / {error_key}")
    except urllib.error.HTTPError as e:
        logger.error(f"[MATRIX] HTTP {e.code}: {e.read().decode(errors='replace')}")
    except Exception as e:
        logger.error(f"[MATRIX] Lỗi gửi thông báo: {e}")


def notify_printer_error(
    device_name: str,
    error_key: str,
    detail: str = "",
    printer_name: str = "Unknown",
) -> None:
    """
    Gửi thông báo lên Matrix (không block). Có cooldown 5 phút/device/lỗi.

    Args:
        device_name: Tên thiết bị (ward 1, ...)
        error_key:   Mã lỗi: paper_jam | no_paper | disconnected | hardware_error | print_failed | ...
        detail:      Mô tả chi tiết lỗi (optional)
        printer_name: Tên máy in (Canon SELPHY CP1500, ...)
    """
    cooldown_key = f"{device_name}:{error_key}"
    now = time.time()

    with _cooldown_lock:
        last_sent = _cooldown.get(cooldown_key, 0.0)
        if now - last_sent < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - last_sent))
            logger.debug(f"[MATRIX] Cooldown {remaining}s — bỏ qua: {cooldown_key}")
            return
        _cooldown[cooldown_key] = now

    thread = threading.Thread(
        target=_send_sync,
        args=(device_name, error_key, detail, printer_name),
        daemon=True,
    )
    thread.start()
