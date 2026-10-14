"""Package the compiled manuscript and its local assets for Overleaf."""

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / 'report'
TEXT_SUFFIXES = {'.tex', '.bib', '.cls', '.sty', '.bst'}


def report_files(require_fresh_pdf=True):
    files = [REPORT / name for name in (
        'main.tex', 'main.pdf', 'references.bib', 'cas-sc.cls',
        'cas-dc.cls', 'cas-common.sty', 'cas-model2-names.bst')]
    for directory, suffixes in (('figures', {'.pdf', '.png'}),
                                ('tables', {'.tex'}), ('thumbnails', {'.jpeg'})):
        files.extend(sorted(p for p in (REPORT / directory).iterdir() if p.suffix in suffixes))
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
    pdf = REPORT / 'main.pdf'
    if require_fresh_pdf and any(p.stat().st_mtime_ns > pdf.stat().st_mtime_ns for p in files if p != pdf):
        raise ValueError('Compile report/main.tex again: the PDF is older than a source or asset')
    return files


def archive_bytes(path):
    """Keep TeX sources stable across Git's LF/CRLF checkout conversion."""
    if path.suffix in TEXT_SUFFIXES:
        return path.read_text(encoding='utf-8').encode('utf-8')
    return path.read_bytes()


def package(output, check=False):
    output = Path(output)
    # A checkout can reorder mtimes. Verification compares contents, while
    # creation additionally guards against the common case of an old PDF.
    files = {p.relative_to(REPORT).as_posix(): archive_bytes(p)
             for p in report_files(require_fresh_pdf=not check)}
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    if check:
        with zipfile.ZipFile(output) as archive:
            if set(archive.namelist()) != set(files) | {'submission_manifest.json'}:
                raise ValueError('Archive file list differs from the current report')
            if json.loads(archive.read('submission_manifest.json')) != manifest:
                raise ValueError('Archive manifest differs from the current report')
            for name, expected in manifest.items():
                if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                    raise ValueError(f'Archive content differs: {name}')
        print(f'Verified {len(files)} report files in {output}')
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(suffix='.zip', dir=output.parent)
    os.close(descriptor)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, data in files.items():
                archive.writestr(name, data)
            archive.writestr('submission_manifest.json', json.dumps(manifest, indent=2) + '\n')
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    package(output, check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'report_overleaf.zip')
    args = parser.parse_args()
    package(args.output, check=args.check)
