"""Batch processing: a DataFrame of links in, a DataFrame of coordinates out."""

from __future__ import annotations

import time
from typing import Optional

import pandas as pd

from .scraper import get_accurate_coords, make_driver
from .url_parser import Coordinates, extract_coords

__all__ = ["extract_dataframe", "DEFAULT_LINK_COLUMN"]

DEFAULT_LINK_COLUMN = "LINK GMAPS"


def extract_dataframe(
    df: pd.DataFrame,
    link_column: str = DEFAULT_LINK_COLUMN,
    use_browser: bool = True,
    delay: float = 0.0,
    limit: Optional[int] = None,
    progress: bool = True,
) -> pd.DataFrame:
    """Add ``Latitude``, ``Longitude`` and ``Source`` columns to ``df``.

    Args:
        df: Input table. Must contain ``link_column``.
        link_column: Name of the column holding the Google Maps links.
        use_browser: ``False`` skips Selenium and parses the links as-is.
            Fine for already-expanded URLs, useless for short links.
        delay: Seconds to pause between rows. Be polite on large batches.
        limit: Process only the first N rows (handy while testing).
        progress: Print a one-line-per-row progress trace.

    Returns:
        A copy of ``df`` with the three extra columns appended. Rows whose link
        is blank or unresolvable get empty strings rather than ``NaN``, so the
        result exports cleanly to Excel.
    """
    if link_column not in df.columns:
        raise KeyError(
            f"Column {link_column!r} not found. Available columns: {list(df.columns)}"
        )

    work = df.head(limit).copy() if limit else df.copy()
    total = len(work)
    driver = make_driver() if use_browser else None
    results: list[Coordinates] = []

    try:
        for position, (_, row) in enumerate(work.iterrows(), start=1):
            url = row[link_column]
            if use_browser:
                coords = get_accurate_coords(url, driver=driver)
            else:
                coords = extract_coords(url if isinstance(url, str) else "")

            results.append(coords)

            if progress:
                status = f"{coords.latitude}, {coords.longitude}" if coords.found else "not found"
                print(f"[{position}/{total}] {status}")

            if delay and position < total:
                time.sleep(delay)
    finally:
        if driver is not None:
            driver.quit()

    coords_df = pd.DataFrame([c.as_dict() for c in results], index=work.index)
    out = pd.concat([work, coords_df], axis=1)

    # Excel-friendly: text columns, empty string instead of None/NaN.
    for column in ("Latitude", "Longitude", "Source"):
        out[column] = out[column].astype("string").fillna("")

    return out
