"""Tests for the model registry (digests come from real files)."""

import hashlib
import json
import unittest
from pathlib import Path
import tempfile

from src.models.registry import load_registry, resolve, sha256_of, validate, verify_entry


def entry(name="m", version="1", digest="a" * 64, status="production"):
    return {"name": name, "version": version, "digest": digest,
            "status": status, "ledger_ref": "R-x-01"}


class RegistryTest(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def write(self, entries):
        path = self.root / "registry.json"
        path.write_text(json.dumps({"models": entries}), encoding="utf-8")
        return path

    def test_project_registry_is_valid_and_matches_files(self):
        registry = Path("docs") / "models" / "registry.json"
        entries = load_registry(registry)
        production = resolve(entries, "phishvision_cnn_v2")

        self.assertEqual(production["status"], "production")
        self.assertEqual(len(production["digest"]), 64)

        model = Path("models") / "phishvision_cnn_v2.pth"
        if model.is_file():
            self.assertTrue(verify_entry(production, model))

    def test_two_production_models_rejected(self):
        with self.assertRaises(ValueError):
            validate([entry(name="a", digest="a" * 64),
                      entry(name="b", digest="b" * 64)])

    def test_no_production_model_rejected(self):
        with self.assertRaises(ValueError):
            validate([entry(status="candidate")])

    def test_duplicate_digest_rejected(self):
        with self.assertRaises(ValueError):
            validate([entry(name="a"), entry(name="b", version="2", status="candidate")])

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            validate([entry(status="blessed")])

    def test_missing_field_rejected(self):
        bad = entry()
        del bad["ledger_ref"]
        with self.assertRaises(ValueError):
            validate([bad])

    def test_resolve_unknown_raises(self):
        with self.assertRaises(KeyError):
            resolve([entry()], "absent")

    def test_verify_entry_detects_wrong_file(self):
        path = self.root / "model.pth"
        path.write_bytes(b"weights")
        good = hashlib.sha256(b"weights").hexdigest().upper()

        self.assertTrue(verify_entry(entry(digest=good), path))
        self.assertFalse(verify_entry(entry(digest="b" * 64), path))

    def test_sha256_of_matches_hashlib(self):
        path = self.root / "f.bin"
        path.write_bytes(b"abc")

        self.assertEqual(sha256_of(path), hashlib.sha256(b"abc").hexdigest().upper())


if __name__ == "__main__":
    unittest.main()
