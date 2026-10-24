"""Tests for the PhishTank importer."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from import_phistank import verified_urls  # noqa: E402


def row(url="https://a.example/x", verified="yes", online="yes"):
    return {"url": url, "verified": verified, "online": online,
            "phish_id": "1", "phish_detail_url": "", "submission_time": "",
            "verification_time": "", "target": ""}


def test_keeps_verified_and_online():
    urls = verified_urls([row(), row("https://b.example/y")])

    assert urls == ["https://a.example/x", "https://b.example/y"]


def test_drops_unverified():
    assert verified_urls([row(verified="no")]) == []


def test_drops_offline():
    assert verified_urls([row(online="no")]) == []


def test_deduplicates():
    urls = verified_urls([row(), row()])

    assert urls == ["https://a.example/x"]


def test_rejects_non_http_values():
    assert verified_urls([row(url="ftp://a.example/x")]) == []


def test_tolerates_upper_case_headers_and_values():
    payload = {"URL": "https://c.example/z", "Verified": "YES", "Online": "YES"}

    assert verified_urls([payload]) == ["https://c.example/z"]
