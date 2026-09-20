"""Generate the synthetic sample dataset shipped in ``data/``.

Every row is a public Indonesian tourist destination with a publicly known
location. No private, customer or business data is involved anywhere in this
repository - running this script is how ``data/sample_tourist_places.xlsx``
came to exist, and you can regenerate it at any time:

    python scripts/make_sample_data.py

The links are written in Google Maps' **expanded** form, which is exactly what
a ``maps.app.goo.gl`` short link resolves to. That keeps the demo reproducible:
short links belong to whoever created them and can expire, so pinning the demo
to them would leave a broken repository behind.

The last six rows are deliberately awkward - a camera-only URL, a query-string
URL, whitespace padding, a tracking suffix, a blank cell and a free-text note where a link should be - so
the extractor's fallback chain and its error handling are both visible in the
sample output.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gmaps_gps.exporter import save_formatted_excel  # noqa: E402

OUT_XLSX = ROOT / "data" / "sample_tourist_places.xlsx"
OUT_CSV = ROOT / "data" / "sample_tourist_places.csv"
SHEET_NAME = "PLACES"

# region, place_id, name, category, province, city, surveyor, lat, lng
PLACES = [
    ("JAWA", "TRP-001", "Candi Borobudur", "Heritage", "Jawa Tengah", "Magelang", "Surveyor A", -7.6078738, 110.2037342),
    ("JAWA", "TRP-002", "Candi Prambanan", "Heritage", "DI Yogyakarta", "Sleman", "Surveyor A", -7.7520188, 110.4915447),
    ("JAWA", "TRP-003", "Keraton Yogyakarta", "Heritage", "DI Yogyakarta", "Yogyakarta", "Surveyor A", -7.8053291, 110.3642537),
    ("JAWA", "TRP-004", "Jalan Malioboro", "Urban", "DI Yogyakarta", "Yogyakarta", "Surveyor B", -7.7925416, 110.3658102),
    ("JAWA", "TRP-005", "Monumen Nasional", "Landmark", "DKI Jakarta", "Jakarta Pusat", "Surveyor B", -6.1753924, 106.8271528),
    ("JAWA", "TRP-006", "Kota Tua Jakarta", "Heritage", "DKI Jakarta", "Jakarta Barat", "Surveyor B", -6.1352073, 106.8133629),
    ("JAWA", "TRP-007", "Taman Mini Indonesia Indah", "Theme Park", "DKI Jakarta", "Jakarta Timur", "Surveyor B", -6.3024188, 106.8951704),
    ("JAWA", "TRP-008", "Gedung Sate", "Landmark", "Jawa Barat", "Bandung", "Surveyor C", -6.9025347, 107.6186215),
    ("JAWA", "TRP-009", "Kawah Putih Ciwidey", "Nature", "Jawa Barat", "Bandung", "Surveyor C", -7.1660492, 107.4022836),
    ("JAWA", "TRP-010", "Dataran Tinggi Dieng", "Nature", "Jawa Tengah", "Banjarnegara", "Surveyor C", -7.2000714, 109.9100328),
    ("JAWA", "TRP-011", "Goa Jomblang", "Cave", "DI Yogyakarta", "Gunungkidul", "Surveyor C", -8.0300529, 110.6400147),
    ("JAWA", "TRP-012", "Gunung Bromo", "Nature", "Jawa Timur", "Probolinggo", "Surveyor D", -7.9425163, 112.9530472),
    ("JAWA", "TRP-013", "Kawah Ijen", "Nature", "Jawa Timur", "Banyuwangi", "Surveyor D", -8.0581294, 114.2421608),
    ("JAWA", "TRP-014", "Air Terjun Tumpak Sewu", "Waterfall", "Jawa Timur", "Lumajang", "Surveyor D", -8.2308457, 112.9200913),
    ("BALI", "TRP-015", "Pantai Kuta", "Beach", "Bali", "Badung", "Surveyor E", -8.7180236, 115.1686794),
    ("BALI", "TRP-016", "Pura Tanah Lot", "Temple", "Bali", "Tabanan", "Surveyor E", -8.6212058, 115.0868341),
    ("BALI", "TRP-017", "Pura Luhur Uluwatu", "Temple", "Bali", "Badung", "Surveyor E", -8.8291427, 115.0849062),
    ("BALI", "TRP-018", "Sacred Monkey Forest Ubud", "Nature", "Bali", "Gianyar", "Surveyor E", -8.5188309, 115.2585176),
    ("BALI", "TRP-019", "Kelingking Beach", "Beach", "Bali", "Klungkung", "Surveyor E", -8.7513642, 115.4715283),
    ("NUSRA", "TRP-020", "Gili Trawangan", "Island", "Nusa Tenggara Barat", "Lombok Utara", "Surveyor F", -8.3500817, 116.0400459),
    ("NUSRA", "TRP-021", "Pulau Padar", "Island", "Nusa Tenggara Timur", "Manggarai Barat", "Surveyor F", -8.6539274, 119.5800638),
    ("NUSRA", "TRP-022", "Danau Kelimutu", "Nature", "Nusa Tenggara Timur", "Ende", "Surveyor F", -8.7667135, 121.8167492),
    ("SUMATERA", "TRP-023", "Danau Toba Parapat", "Lake", "Sumatera Utara", "Simalungun", "Surveyor G", -2.6845731, 98.9350264),
    ("SUMATERA", "TRP-024", "Istana Maimun", "Heritage", "Sumatera Utara", "Medan", "Surveyor G", 3.5752408, 98.6837159),
    ("SUMATERA", "TRP-025", "Jam Gadang", "Landmark", "Sumatera Barat", "Bukittinggi", "Surveyor G", -0.3050682, 100.3692374),
    ("SUMATERA", "TRP-026", "Masjid Raya Baiturrahman", "Heritage", "Aceh", "Banda Aceh", "Surveyor G", 5.5544219, 95.3175806),
    ("SUMATERA", "TRP-027", "Pantai Tanjung Tinggi", "Beach", "Kepulauan Bangka Belitung", "Belitung", "Surveyor H", -2.5500365, 107.6400718),
    ("SULAWESI", "TRP-028", "Pantai Losari", "Beach", "Sulawesi Selatan", "Makassar", "Surveyor H", -5.1440592, 119.4090247),
    ("SULAWESI", "TRP-029", "Taman Nasional Bunaken", "Marine", "Sulawesi Utara", "Manado", "Surveyor H", 1.6200483, 124.7600915),
    ("PAPUA", "TRP-030", "Piaynemo Raja Ampat", "Island", "Papua Barat Daya", "Raja Ampat", "Surveyor H", -0.5683126, 130.2717504),
]

# Awkward-on-purpose rows: region, id, name, category, province, city, surveyor, link
EDGE_CASES = [
    ("JAWA", "TRP-031", "Pantai Parangtritis", "Beach", "DI Yogyakarta", "Bantul", "Surveyor B",
     "https://www.google.com/maps/@-8.0255,110.3300,15z"),
    ("SUMATERA", "TRP-032", "Taman Nasional Way Kambas", "Nature", "Lampung", "Lampung Timur", "Surveyor G",
     "https://www.google.com/maps?q=-4.9300,105.7500"),
    ("JAWA", "TRP-033", "Benteng Vredeburg", "Heritage", "DI Yogyakarta", "Yogyakarta", "Surveyor A",
     "  https://www.google.com/maps/place/Benteng+Vredeburg/@-7.8000,110.3660,17z/data=!4m6!3m5!1s0x0:0x0!8m2!3d-7.8001234!4d110.3661234  "),
    ("NUSRA", "TRP-034", "Pantai Pink Lombok", "Beach", "Nusa Tenggara Barat", "Lombok Timur", "Surveyor F",
     "https://www.google.com/maps/place/Pantai+Pink/@-8.8800,116.5500,17z/data=!4m6!3m5!1s0x0:0x0!8m2!3d-8.8801111!4d116.5502222?g_st=iw"),
    ("SUMATERA", "TRP-035", "Pulau Weh Sabang", "Island", "Aceh", "Sabang", "Surveyor G", ""),
    ("JAWA", "TRP-036", "Green Canyon Pangandaran", "Nature", "Jawa Barat", "Pangandaran", "Surveyor C", "belum ada link"),
]

COLUMNS = [
    "REGION", "PLACE ID", "PLACE NAME", "CATEGORY",
    "PROVINCE", "CITY", "SURVEYOR", "LINK GMAPS",
]


def build_maps_url(name: str, lat: float, lng: float) -> str:
    """Build a Google Maps URL in the shape a share link resolves to.

    The camera centre (``@lat,lng``) is offset slightly from the map pin
    (``!3d``/``!4d``) exactly as Google does it - that gap is the whole reason
    the extractor prefers the pin over the camera.
    """
    slug = quote(name.replace(" ", "+"), safe="+")
    cam_lat, cam_lng = round(lat + 0.0000164, 7), round(lng + 0.0000891, 7)
    return (
        f"https://www.google.com/maps/place/{slug}"
        f"/@{cam_lat},{cam_lng},17z"
        f"/data=!3m1!4b1!4m6!3m5!1s0x0:0x0!8m2!3d{lat}!4d{lng}!16s%2Fg%2F11f0sample"
    )


def build_dataframe() -> pd.DataFrame:
    rows = [
        (region, pid, name, category, province, city, surveyor,
         build_maps_url(name, lat, lng))
        for region, pid, name, category, province, city, surveyor, lat, lng in PLACES
    ]
    rows.extend(EDGE_CASES)
    return pd.DataFrame(rows, columns=COLUMNS)


def main() -> None:
    df = build_dataframe()
    save_formatted_excel(df, OUT_XLSX, sheet_name=SHEET_NAME)
    df.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_XLSX} and {OUT_CSV} ({len(df)} rows)")


if __name__ == "__main__":
    main()
