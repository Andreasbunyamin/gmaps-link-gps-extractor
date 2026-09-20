"""Resolve Google Maps short links with a headless Chrome session.

A ``maps.app.goo.gl/XXXX`` link cannot be expanded with a plain HTTP redirect:
Google answers with a JavaScript interstitial and, in most regions, a cookie
consent page. A real browser is the reliable way through both, so Selenium
drives the redirect and we read the coordinates out of the final URL.

Importing this module does not require Selenium; the dependency is only
resolved when a driver is actually created, so the pure parser and the
``--no-browser`` pipeline stay importable in a bare environment.
"""

from __future__ import annotations

import time
from typing import Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from .url_parser import Coordinates, extract_coords, is_valid_url

__all__ = ["make_driver", "resolve_url", "get_accurate_coords", "CONSENT_COOKIE"]

CONSENT_HOST = "consent.google.com"
GOOGLE_HOME = "https://www.google.com"

#: Cookie that tells Google the consent dialog has already been answered.
#: This is a generic, account-independent value - it carries no personal data.
CONSENT_COOKIE = {
    "name": "SOCS",
    "value": "CAESEwgDEgk0ODE3Nzk3MjMaAmVuIAEaBgiA_LyaBg",
    "domain": ".google.com",
    "path": "/",
    "secure": True,
    "httpOnly": False,
}

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT = 20
SETTLE_SECONDS = 2


def make_driver(headless: bool = True, user_agent: str = DEFAULT_USER_AGENT):
    """Create a Chrome driver with the consent cookie already injected.

    Reuse one driver for a whole batch - starting Chrome per row is what makes
    naive versions of this script take hours instead of minutes.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--user-agent={user_agent}")

    driver = webdriver.Chrome(options=options)
    _inject_consent_cookie(driver)
    return driver


def _inject_consent_cookie(driver) -> None:
    """Visit google.com once so the consent cookie has a domain to attach to."""
    driver.get(GOOGLE_HOME)
    time.sleep(1)
    driver.add_cookie(CONSENT_COOKIE)


def resolve_url(driver, url: str, timeout: int = DEFAULT_TIMEOUT) -> Tuple[str, str]:
    """Follow ``url`` to its final destination and return ``(final_url, html)``."""
    from selenium.webdriver.support.ui import WebDriverWait

    driver.get(url)
    _wait_for(driver, timeout, lambda d: "!3d" in d.current_url or CONSENT_HOST in d.current_url)

    # Consent interstitial: the real destination is in the ?continue= parameter.
    if CONSENT_HOST in driver.current_url:
        params = parse_qs(urlparse(driver.current_url).query)
        if "continue" in params:
            destination = unquote(params["continue"][0])
            _inject_consent_cookie(driver)
            driver.get(destination)
            _wait_for(
                driver, timeout,
                lambda d: "!3d" in d.current_url or "@" in d.current_url,
            )

    return driver.current_url, driver.page_source


def _wait_for(driver, timeout: int, condition) -> None:
    """Wait for ``condition``; a timeout is not fatal - we parse what we have."""
    from selenium.webdriver.support.ui import WebDriverWait

    try:
        WebDriverWait(driver, timeout).until(condition)
        time.sleep(SETTLE_SECONDS)
    except Exception:
        pass


def get_accurate_coords(
    url: str,
    driver=None,
    timeout: int = DEFAULT_TIMEOUT,
    use_browser: bool = True,
) -> Coordinates:
    """Return the coordinates behind a single Google Maps link.

    Args:
        url: A short (``maps.app.goo.gl/...``) or full Google Maps URL.
        driver: An existing Selenium driver to reuse. When omitted a throwaway
            driver is created and closed again.
        timeout: Seconds to wait for the redirect to settle.
        use_browser: Set to ``False`` to parse the URL as given, with no
            browser at all. Only works on links that are already expanded.
    """
    if not is_valid_url(url):
        return Coordinates()

    if not use_browser:
        return extract_coords(url)

    owns_driver = driver is None
    if owns_driver:
        driver = make_driver()

    try:
        final_url, html = resolve_url(driver, url, timeout=timeout)
        return extract_coords(final_url, html)
    except Exception as exc:  # noqa: BLE001 - one bad row must not kill the batch
        print(f"  ! could not resolve {url[:60]}: {exc}")
        return Coordinates()
    finally:
        if owns_driver:
            driver.quit()
