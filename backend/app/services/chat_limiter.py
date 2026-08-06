"""In-memory рейт-лимит для /chat — защита платного Claude API от абьюза.
Не персистентный (сбрасывается при рестарте бэкенда) — это ок для лимита
"N сообщений в час на IP", в отличие от заявок пользователей в reports_db,
это не данные, которые нужно хранить."""
import time
from collections import defaultdict

from app.services.reports_db import ip_hash

RATE_LIMIT_PER_HOUR = 20
_WINDOW_SECONDS = 3600

_hits: dict[str, list[float]] = defaultdict(list)


def rate_limited(ip: str) -> bool:
    h = ip_hash(ip)
    now = time.time()
    recent = [t for t in _hits[h] if now - t < _WINDOW_SECONDS]
    _hits[h] = recent
    if len(recent) >= RATE_LIMIT_PER_HOUR:
        return True
    recent.append(now)
    return False
