"""Hash-guided repair must not erase corruption present in the original source."""
import hashlib
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('build_db', Path(__file__).resolve().parents[1] / 'scripts/build_db.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def row(source, exported=None):
    raw = source.encode('utf8')
    return dict(rev_id='example@1', body=source if exported is None else exported,
                body_encoding='utf8', body_sha256=hashlib.sha256(raw).hexdigest(), body_len=len(raw))


class RevisionDecodingTests(unittest.TestCase):
    def test_valid_original_is_preserved(self):
        data = row('“Quoted text”')
        self.assertEqual(build.normalize_revision_body(data), data)

    def test_export_layer_is_removed_without_erasing_historical_corruption(self):
        source = '“Quoted text”'.encode('utf8').decode('latin1')
        exported = source.encode('utf8').decode('latin1')
        self.assertEqual(build.normalize_revision_body(row(source, exported))['body'], source)

    def test_unverified_text_is_rejected(self):
        with self.assertRaises(ValueError):
            build.normalize_revision_body(row('original', 'different'))

    def test_inconsistent_length_is_rejected(self):
        data = row('original')
        data['body_len'] = 1
        with self.assertRaises(ValueError):
            build.normalize_revision_body(data)
