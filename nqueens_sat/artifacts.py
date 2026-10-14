"""Portable fingerprints for text artifacts; binary files retain byte hashes."""

import hashlib
from pathlib import Path

TEXT_HASH_POLICY = 'sha256-utf8-lf-v1'


def text_sha256(path):
    # Only newline representation is normalized; data and whitespace stay intact.
    contents = Path(path).read_text(encoding='utf-8')
    return hashlib.sha256(contents.encode('utf-8')).hexdigest()
