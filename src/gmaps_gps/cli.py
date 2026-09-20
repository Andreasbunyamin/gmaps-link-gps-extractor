"""Command-line interface.

Every path, sheet name and column name is an argument or an environment
variable - nothing about a particular dataset is baked into the code.

    python -m gmaps_gps --input data/sample_tourist_places.xlsx --no-browser
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

from .exporter import save_formatted_excel
from .pipeline import DEFAULT_LINK_COLUMN, extract_dataframe

DEFAULT_INPUT = os.getenv("GMAPS_INPUT_FILE", "data/sample_tourist_places.xlsx")
DEFAULT_SHEET = os.getenv("GMAPS_INPUT_SHEET", "PLACES")
DEFAULT_OUTPUT = os.getenv("GMAPS_OUTPUT_FILE", "output/gps_coordinates.xlsx")
DEFAULT_COLUMN = os.getenv("GMAPS_LINK_COLUMN", DEFAULT_LINK_COLUMN)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gmaps_gps",
        description="Extract latitude/longitude from a column of Google Maps links.",
    )
    parser.add_argument("-i", "--input", default=DEFAULT_INPUT,
                        help=f"Input .xlsx or .csv file (default: {DEFAULT_INPUT})")
    parser.add_argument("-s", "--sheet", default=DEFAULT_SHEET,
                        help=f"Worksheet name for .xlsx input (default: {DEFAULT_SHEET})")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT,
                        help=f"Output .xlsx file (default: {DEFAULT_OUTPUT})")
    parser.add_argument("-c", "--link-column", default=DEFAULT_COLUMN,
                        help=f"Column holding the links (default: {DEFAULT_COLUMN!r})")
    parser.add_argument("--no-browser", action="store_true",
                        help="Parse links as given, without Selenium. Works only "
                             "for already-expanded URLs, not for short links.")
    parser.add_argument("--delay", type=float, default=0.0,
                        help="Seconds to pause between rows (default: 0)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process only the first N rows")
    parser.add_argument("--csv", action="store_true",
                        help="Also write a .csv next to the .xlsx output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress per-row output")
    return parser


def read_table(path: Path, sheet: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path, sheet_name=sheet)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = Path(args.input)

    df = read_table(source, args.sheet)
    print(f"Loaded {len(df)} rows from {source}")

    result = extract_dataframe(
        df,
        link_column=args.link_column,
        use_browser=not args.no_browser,
        delay=args.delay,
        limit=args.limit,
        progress=not args.quiet,
    )

    written = save_formatted_excel(result, args.output, sheet_name="GPS")
    if args.csv:
        csv_path = Path(args.output).with_suffix(".csv")
        result.to_csv(csv_path, index=False)
        print(f"Wrote {csv_path}")

    found = int((result["Latitude"] != "").sum())
    print(f"Wrote {written}")
    print(f"Resolved {found}/{len(result)} links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
