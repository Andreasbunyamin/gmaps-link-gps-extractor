"""Pure coordinate-extraction logic.

Everything in this module works on plain strings (a URL and, optionally, the
page HTML). No browser, no network. That makes the interesting part of the
project unit-testable and lets the pipeline run in ``--no-browser`` mode on
links that are already expanded.

Extraction is a priority chain: the earlier a strategy sits in the list, the
more trustworthy its coordinates are. The name of the winning strategy is
returned alongside the coordinates so you can tell a precise map pin apart
from a rough camera position.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlparse

__all__ = ["Coordinates", "clean_coord", "extract_coords", "STRATEGY_ORDER"]

# A decimal degree value, e.g. "-7.6078738". Latitude/longitude only ever have
# 1-3 digits before the decimal point.
_DECIMAL = r"-?\d{1,3}\.\d+"

# Map pin ("!3d<lat>!4d<lng>"): the exact location of the marker.
_PIN_LAT_RE = re.compile(rf"!3d({_DECIMAL})")
_PIN_LNG_RE = re.compile(rf"!4d({_DECIMAL})")
_PIN_PAIR_RE = re.compile(rf"!3d({_DECIMAL})!4d({_DECIMAL})")

# Camera position ("@<lat>,<lng>,17z"): where the viewport is centred, which is
# close to the pin but not identical to it.
_CAMERA_RE = re.compile(rf"@({_DECIMAL}),({_DECIMAL})")
_PLACE_CAMERA_RE = re.compile(rf"/place/[^/]+/@({_DECIMAL}),({_DECIMAL})")

# "?q=-7.60,110.20" style query parameters.
_QUERY_PAIR_RE = re.compile(rf"({_DECIMAL}),\s*({_DECIMAL})")

# Last resort: any high-precision pair anywhere in the URL.
_LOOSE_PAIR_RE = re.compile(r"(-?\d{1,3}\.\d{4,}),(-?\d{1,3}\.\d{4,})")

# Coordinates embedded in the page's inlined JS payload.
_JS_ARRAY_RE = re.compile(rf"\[null,null,({_DECIMAL}),({_DECIMAL})\]")

_STRICT_COORD_RE = re.compile(rf"^{_DECIMAL}$")

_QUERY_KEYS = ("q", "query", "ll", "daddr", "center")

STRATEGY_ORDER = (
    "pin_url",      # !3d/!4d in the resolved URL          - exact
    "pin_html",     # !3d/!4d in the page source           - exact
    "camera_url",   # @lat,lng viewport centre             - approximate
    "place_url",    # /place/<name>/@lat,lng               - approximate
    "query_param",  # ?q= / ?ll= / ?query=                 - as supplied
    "loose_url",    # any lat,lng pair in the URL          - unverified
    "js_html",      # [null,null,lat,lng] in page source   - unverified
)

#: Strategies whose result is the marker itself rather than an approximation.
EXACT_STRATEGIES = frozenset({"pin_url", "pin_html"})


@dataclass(frozen=True)
class Coordinates:
    """Result of one extraction attempt."""

    latitude: Optional[str] = None
    longitude: Optional[str] = None
    source: Optional[str] = None

    @property
    def found(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    @property
    def is_exact(self) -> bool:
        """True when the coordinates came from the map pin, not the camera."""
        return self.source in EXACT_STRATEGIES

    def as_dict(self) -> dict:
        return {
            "Latitude": self.latitude,
            "Longitude": self.longitude,
            "Source": self.source,
        }


def clean_coord(value: Optional[str]) -> Optional[str]:
    """Return ``value`` stripped if it is a bare decimal degree, else ``None``."""
    if not value:
        return None
    candidate = str(value).strip()
    return candidate if _STRICT_COORD_RE.match(candidate) else None


def _pair(lat: Optional[str], lng: Optional[str], source: str) -> Optional[Coordinates]:
    lat, lng = clean_coord(lat), clean_coord(lng)
    if lat is None or lng is None:
        return None
    if not (-90 <= float(lat) <= 90 and -180 <= float(lng) <= 180):
        return None
    return Coordinates(lat, lng, source)


def is_valid_url(url) -> bool:
    """True for a non-empty string that looks like an http(s) link."""
    return bool(url) and isinstance(url, str) and url.strip().lower().startswith("http")


def extract_coords(url: str, html: str = "") -> Coordinates:
    """Pull the best available latitude/longitude out of a URL and page source.

    Args:
        url: The **resolved** Google Maps URL (a short ``maps.app.goo.gl`` link
            has to be followed first - see :mod:`gmaps_gps.scraper`).
        html: Optional page source, used only by the HTML-based fallbacks.

    Returns:
        A :class:`Coordinates`. When nothing matches, every field is ``None``.
    """
    if not is_valid_url(url):
        return Coordinates()

    url = url.strip()

    # 1. Map pin in the URL - the marker itself.
    hit = _pair(
        _first(_PIN_LAT_RE, url), _first(_PIN_LNG_RE, url), "pin_url"
    )
    if hit:
        return hit

    # 2. Map pin in the page source - same precision, different place to look.
    if html:
        match = _PIN_PAIR_RE.search(html)
        if match:
            hit = _pair(match.group(1), match.group(2), "pin_html")
            if hit:
                return hit

    # 3. Camera centre - close to the pin, usually a few metres off.
    match = _CAMERA_RE.search(url)
    if match:
        hit = _pair(match.group(1), match.group(2), "camera_url")
        if hit:
            return hit

    # 4. /place/<name>/@lat,lng - same idea, stricter shape.
    match = _PLACE_CAMERA_RE.search(url)
    if match:
        hit = _pair(match.group(1), match.group(2), "place_url")
        if hit:
            return hit

    # 5. Coordinates handed over as a query parameter.
    params = parse_qs(urlparse(url).query)
    for key in _QUERY_KEYS:
        if key in params:
            match = _QUERY_PAIR_RE.match(params[key][0])
            if match:
                hit = _pair(match.group(1), match.group(2), "query_param")
                if hit:
                    return hit

    # 6. Any high-precision pair left in the URL.
    match = _LOOSE_PAIR_RE.search(url)
    if match:
        hit = _pair(match.group(1), match.group(2), "loose_url")
        if hit:
            return hit

    # 7. Coordinates in the inlined JS payload.
    if html:
        match = _JS_ARRAY_RE.search(html)
        if match:
            hit = _pair(match.group(1), match.group(2), "js_html")
            if hit:
                return hit

    return Coordinates()


def _first(pattern: re.Pattern, text: str) -> Optional[str]:
    match = pattern.search(text)
    return match.group(1) if match else None
