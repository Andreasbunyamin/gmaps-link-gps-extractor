"""Extract GPS coordinates from Google Maps share links.

Typical use::

    from gmaps_gps import extract_coords, get_accurate_coords

    extract_coords(full_url)              # no browser, already-expanded URL
    get_accurate_coords(short_url)        # headless Chrome follows the redirect
"""

from .exporter import save_formatted_excel
from .pipeline import DEFAULT_LINK_COLUMN, extract_dataframe
from .scraper import get_accurate_coords, make_driver, resolve_url
from .url_parser import Coordinates, clean_coord, extract_coords

__version__ = "1.0.0"

__all__ = [
    "Coordinates",
    "clean_coord",
    "extract_coords",
    "get_accurate_coords",
    "make_driver",
    "resolve_url",
    "extract_dataframe",
    "save_formatted_excel",
    "DEFAULT_LINK_COLUMN",
    "__version__",
]
