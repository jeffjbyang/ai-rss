from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PREFIXES = ("utm_",)
TRACKING_PARAMS = {"ref", "source"}


def canonical_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.startswith(TRACKING_PREFIXES) and key not in TRACKING_PARAMS
    ]
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/") or parts.path,
            urlencode(query),
            "",
        )
    )
