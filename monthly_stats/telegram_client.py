import os
from typing import Any, Dict, Optional

import requests

from monthly_stats.config import REQUEST_TIMEOUT


TELEGRAM_SEND_MESSAGE_URL_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram_message(text: str) -> Optional[Dict[str, Any]]:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[telegram] warning: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing, skipping Telegram stage", flush=True)
        return None

    response = requests.post(
        TELEGRAM_SEND_MESSAGE_URL_TEMPLATE.format(token=token),
        json={
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code != 200:
        raise RuntimeError(f"Telegram sendMessage failed: HTTP {response.status_code} | {response.text}")

    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram sendMessage returned non-ok response: {payload}")

    result = payload.get("result") or {}
    message_id = result.get("message_id")
    print(f"[telegram] posted_message_id={message_id}", flush=True)
    return result
