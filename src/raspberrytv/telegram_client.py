from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import validate_url


URL_PATTERN = re.compile(r"(?:^|\s)(https?://[^\s<>]+)", re.IGNORECASE)


def extract_url(text: str) -> str | None:
    text = (text or "").strip()
    if text[:4].lower() == "url ":
        text = text[4:].strip()
    match = URL_PATTERN.search(text)
    if not match:
        return None
    candidate = match.group(1).rstrip(".,;:!?)\"]}")
    try:
        return validate_url(candidate)
    except ValueError:
        return None


@dataclass(frozen=True)
class TelegramSelection:
    url: str | None
    newest_update_id: int
    message_id: int | None = None
    message_date: int | None = None


def select_latest_url(
    updates: list[dict[str, Any]], chat_id: str, topic_id: str = ""
) -> TelegramSelection:
    expected_chat = str(chat_id)
    expected_topic = str(topic_id) if topic_id else ""
    candidates: list[tuple[int, int, str, int, int]] = []
    newest_update_id = 0
    for update in updates:
        update_id = int(update.get("update_id", 0))
        newest_update_id = max(newest_update_id, update_id)
        message = update.get("message") or update.get("channel_post") or {}
        chat = message.get("chat") or {}
        if str(chat.get("id", "")) != expected_chat:
            continue
        actual_topic = str(message.get("message_thread_id", ""))
        if expected_topic and actual_topic != expected_topic:
            continue
        url = extract_url(str(message.get("text", "")))
        if url:
            candidates.append(
                (int(message.get("date", 0)), update_id, url, int(message.get("message_id", 0)), update_id)
            )
    if not candidates:
        return TelegramSelection(None, newest_update_id)
    date, _, url, message_id, update_id = max(candidates)
    return TelegramSelection(url, newest_update_id, message_id, date)


class TelegramClient:
    def __init__(
        self,
        token: str,
        api_root: str = "https://api.telegram.org",
        opener: Callable[..., Any] = urlopen,
    ):
        if not token:
            raise ValueError("Token Telegram non configurato")
        self.token = token
        self.api_root = api_root.rstrip("/")
        self.opener = opener

    def get_updates(self, offset: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        query = urlencode({"offset": max(0, offset), "limit": min(max(limit, 1), 100), "timeout": 0})
        url = f"{self.api_root}/bot{self.token}/getUpdates?{query}"
        request = Request(url, headers={"User-Agent": "RaspberryTV/1"})
        with self.opener(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not payload.get("ok") or not isinstance(payload.get("result"), list):
            raise RuntimeError("Risposta Telegram non valida")
        return payload["result"]
