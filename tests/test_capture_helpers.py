"""Tests for the capture helper's pure functions (no browser needed)."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from capture_pages import registered_domain, split_for  # noqa: E402


def test_registered_domain_simple():
    assert registered_domain("https://login.example.com/path?q=1") == "example.com"


def test_registered_domain_two_part_tld():
    assert registered_domain("https://www.example.co.uk/x") == "example.co.uk"


def test_registered_domain_bare_host():
    assert registered_domain("https://example.com") == "example.com"


def test_split_is_stable_per_domain():
    first = split_for("example.com")
    for _ in range(5):
        assert split_for("example.com") == first


def test_split_values_are_valid():
    for domain in ("a.com", "b.org", "c.net", "d.co.uk", "e.io"):
        assert split_for(domain) in {"train", "validation", "test"}


def test_split_never_mixes_domains_by_construction():
    # Same domain always maps to one split, which is what keeps a kit whole.
    domains = ["x.com", "x.com", "y.com"]
    assert len({split_for(d) for d in domains if d == "x.com"}) == 1
