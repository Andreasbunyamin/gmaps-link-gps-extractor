"""Tests for the coordinate extraction logic.

No browser, no network - these run in under a second and are what CI checks.
"""

import pytest

from gmaps_gps.url_parser import Coordinates, clean_coord, extract_coords, is_valid_url

PIN_URL = (
    "https://www.google.com/maps/place/Candi+Borobudur"
    "/@-7.6078574,110.2038233,17z"
    "/data=!3m1!4b1!4m6!3m5!1s0x0:0x0!8m2!3d-7.6078738!4d110.2037342!16s%2Fg%2F11f0sample"
)


# --------------------------------------------------------------------------
# clean_coord
# --------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("-7.6078738", "-7.6078738"),
    ("  110.2037342  ", "110.2037342"),
    ("0.0", "0.0"),
])
def test_clean_coord_accepts_decimal_degrees(raw, expected):
    assert clean_coord(raw) == expected


@pytest.mark.parametrize("raw", ["", None, "abc", "-7", "-7.60,110.20", "1e5", "--7.6"])
def test_clean_coord_rejects_anything_else(raw):
    assert clean_coord(raw) is None


# --------------------------------------------------------------------------
# is_valid_url
# --------------------------------------------------------------------------

@pytest.mark.parametrize("value", ["", None, float("nan"), "belum ada link", "ftp://x", 42])
def test_is_valid_url_rejects_non_links(value):
    assert is_valid_url(value) is False


def test_is_valid_url_accepts_http_links():
    assert is_valid_url("https://maps.app.goo.gl/abc123") is True


# --------------------------------------------------------------------------
# extract_coords - priority chain
# --------------------------------------------------------------------------

def test_map_pin_wins_over_camera():
    """!3d/!4d is the marker; @lat,lng is only where the viewport sits."""
    result = extract_coords(PIN_URL)
    assert (result.latitude, result.longitude) == ("-7.6078738", "110.2037342")
    assert result.source == "pin_url"
    assert result.is_exact


def test_camera_used_when_no_pin_present():
    result = extract_coords("https://www.google.com/maps/@-8.0255,110.3300,15z")
    assert (result.latitude, result.longitude) == ("-8.0255", "110.3300")
    assert result.source == "camera_url"
    assert not result.is_exact


def test_query_parameter_format():
    result = extract_coords("https://www.google.com/maps?q=-4.9300,105.7500")
    assert (result.latitude, result.longitude) == ("-4.9300", "105.7500")
    assert result.source == "query_param"


def test_pin_found_in_html_when_url_has_none():
    url = "https://www.google.com/maps/place/Somewhere"
    html = "<script>...!3d-6.1753924!4d106.8271528...</script>"
    result = extract_coords(url, html=html)
    assert (result.latitude, result.longitude) == ("-6.1753924", "106.8271528")
    assert result.source == "pin_html"


def test_javascript_array_fallback():
    url = "https://www.google.com/maps/place/Somewhere"
    html = "callback([null,null,-8.6539274,119.5800638])"
    result = extract_coords(url, html=html)
    assert result.source == "js_html"


def test_url_fallback_beats_html_fallback():
    """A coordinate in the URL is preferred over one dug out of the page."""
    url = "https://www.google.com/maps/@-8.0255,110.3300,15z"
    html = "[null,null,-1.1111111,101.1111111]"
    assert extract_coords(url, html=html).source == "camera_url"


# --------------------------------------------------------------------------
# extract_coords - messy real-world input
# --------------------------------------------------------------------------

def test_surrounding_whitespace_is_tolerated():
    result = extract_coords(f"   {PIN_URL}   ")
    assert result.latitude == "-7.6078738"


def test_tracking_suffix_does_not_break_parsing():
    result = extract_coords(f"{PIN_URL}?g_st=iw")
    assert result.latitude == "-7.6078738"


@pytest.mark.parametrize("value", ["", None, "   ", "belum ada link", float("nan"), 0])
def test_unusable_input_returns_empty_result(value):
    result = extract_coords(value)
    assert result == Coordinates()
    assert not result.found


def test_out_of_range_values_are_rejected():
    """A 3-digit 'latitude' is a false positive, not a location."""
    result = extract_coords("https://www.google.com/maps/@999.1234567,110.2037342,17z")
    assert not result.found


def test_positive_and_negative_hemispheres():
    north = extract_coords("https://www.google.com/maps/@5.5544219,95.3175806,17z")
    south = extract_coords("https://www.google.com/maps/@-8.0255000,110.3300000,15z")
    assert north.latitude.startswith("5.")
    assert south.latitude.startswith("-8.")


def test_result_is_serialisable_for_dataframes():
    assert extract_coords(PIN_URL).as_dict() == {
        "Latitude": "-7.6078738",
        "Longitude": "110.2037342",
        "Source": "pin_url",
    }
