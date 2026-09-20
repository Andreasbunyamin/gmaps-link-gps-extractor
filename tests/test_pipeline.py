"""End-to-end tests for the batch pipeline, running against the sample data."""

from pathlib import Path

import pandas as pd
import pytest

from gmaps_gps.exporter import save_formatted_excel
from gmaps_gps.pipeline import extract_dataframe

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_tourist_places.csv"


@pytest.fixture(scope="module")
def sample_df() -> pd.DataFrame:
    return pd.read_csv(SAMPLE)


@pytest.fixture(scope="module")
def processed(sample_df) -> pd.DataFrame:
    return extract_dataframe(sample_df, use_browser=False, progress=False)


def test_sample_data_is_present(sample_df):
    assert len(sample_df) > 0
    assert "LINK GMAPS" in sample_df.columns


def test_output_keeps_input_columns_and_adds_three(sample_df, processed):
    assert list(processed.columns) == list(sample_df.columns) + ["Latitude", "Longitude", "Source"]
    assert len(processed) == len(sample_df)


def test_most_links_resolve(processed):
    resolved = (processed["Latitude"] != "").sum()
    assert resolved >= len(processed) - 2  # two rows have no usable link by design


def test_unresolvable_rows_are_blank_not_nan(processed):
    """Empty strings export to Excel cleanly; NaN shows up as the text 'nan'."""
    unresolved = processed[processed["Latitude"] == ""]
    assert len(unresolved) == 2
    assert not processed[["Latitude", "Longitude", "Source"]].isna().any().any()


def test_borobudur_resolves_to_its_known_pin(processed):
    row = processed.loc[processed["PLACE NAME"] == "Candi Borobudur"].iloc[0]
    assert row["Latitude"] == "-7.6078738"
    assert row["Longitude"] == "110.2037342"
    assert row["Source"] == "pin_url"


def test_source_column_flags_lower_confidence_rows(processed):
    sources = set(processed["Source"]) - {""}
    assert "pin_url" in sources
    assert {"camera_url", "query_param"} & sources, "fallback rows should be visible"


def test_limit_argument(sample_df):
    assert len(extract_dataframe(sample_df, use_browser=False, limit=5, progress=False)) == 5


def test_missing_link_column_raises(sample_df):
    with pytest.raises(KeyError, match="LINK"):
        extract_dataframe(sample_df, link_column="NOT A COLUMN", use_browser=False)


def test_excel_export_round_trip(processed, tmp_path):
    target = save_formatted_excel(processed, tmp_path / "nested" / "out.xlsx", sheet_name="GPS")
    assert target.exists()
    reloaded = pd.read_excel(target, sheet_name="GPS")
    assert len(reloaded) == len(processed)
    assert "Latitude" in reloaded.columns
