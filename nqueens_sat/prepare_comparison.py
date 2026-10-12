"""Check recorded repetitions and build the manuscript's common-size view.

Each cell selects exactly one session. Historical records are never rewritten.
Run this before visualize.py; --check verifies generated CSV/table consistency.
"""
import argparse
import csv
import hashlib
import io
import json
import statistics
from pathlib import Path

from run_benchmark import METRICS, SOLVERS
from test_validation import amo_counts
from utils import validate_solution

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / 'results' / 'benchmarks'
SIZES = (20, 50, 100, 150, 200)
NAMES = ('BinomialEncoder', 'BinaryEncoder', 'CommanderEncoder',
         'SequentialEncoder', 'ProductEncoder', 'ILP-PuLP-CBC',
         'ILP-Gurobi', 'ILP-CPLEX', 'CP-CPLEX', 'CP-SAT-ORTools')
LABELS = ('Binomial', 'Binary', 'Commander', 'Sequential', 'Product',
          'CBC', 'Gurobi', 'CPLEX MIP', 'CP Optimizer', 'CP-SAT')


def read_csv(path):
    with path.open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def check_session(directory):
    raw = read_csv(directory / 'raw.csv')
    summaries = read_csv(directory / 'summary.csv')
    metadata = json.loads((directory / 'metadata.json').read_text(encoding='utf-8'))
    assert len({(r['encoder_name'], r['n'], r['repeat']) for r in raw}) == len(raw)
    assert metadata['solver_workers'] == 1 and metadata['wall_limit_seconds_per_repeat'] == 120
    for summary in summaries:
        rows = [r for r in raw if (r['encoder_name'], r['n']) == (summary['encoder_name'], summary['n'])]
        assert len(rows) == int(summary['n_repeats']) == 3
        successful = [r for r in rows if r['status'] in ('SAT', 'UNSAT')]
        assert len(successful) == int(summary['n_success'])
        assert {r['status'] for r in rows} == {summary['status']}, (directory, summary)
        for row in successful:
            assert abs(float(row['encoding_time']) + float(row['solving_time']) - float(row['total_time'])) < 1e-9
        for metric in METRICS:
            if metric not in summary:
                continue  # Old sessions did not record separate setup times.
            values = [float(r[metric]) for r in successful if r.get(metric) not in ('', None)]
            expected = statistics.median(values) if len(values) == 3 else None
            actual = summary[metric]
            assert (actual == '' and expected is None) or (expected is not None and abs(float(actual) - expected) < 1e-9), (directory, metric)
    witnesses = directory / 'runs.jsonl'
    if witnesses.exists():
        records = [json.loads(line) for line in witnesses.read_text(encoding='utf-8').splitlines()]
        assert len(records) == len(raw)
        for row, record in zip(raw, records):
            for key in ('encoder_name', 'n', 'repeat', 'status'):
                assert str(record[key]) == row[key]
            if record['status'] == 'SAT':
                assert validate_solution([tuple(pair) for pair in record['solution']], record['n'])
            for metric in METRICS:
                if row.get(metric) not in ('', None):
                    assert float(row[metric]) == record[metric]
    return summaries, metadata, witnesses.exists()


def build(check=False):
    sessions = ('common_small_benchmark', 'large_n_benchmark',
                'cplex_standard_benchmark', 'gurobi_corrected_benchmark')
    loaded = {s: check_session(DATA / s) for s in sessions}
    assert loaded['gurobi_corrected_benchmark'][2], 'Corrected Gurobi runs must retain witnesses'
    rows = []
    for name in NAMES:
        for n in SIZES:
            session = ('gurobi_corrected_benchmark' if name == 'ILP-Gurobi' else
                       'cplex_standard_benchmark' if name in ('ILP-CPLEX', 'CP-CPLEX') else
                       'common_small_benchmark' if n <= 100 else 'large_n_benchmark')
            candidates = [r for r in loaded[session][0] if r['encoder_name'] == name and int(r['n']) == n]
            assert len(candidates) == 1
            row = dict(candidates[0])
            row['source_dataset'] = session
            row['witnesses_retained'] = loaded[session][2]
            row['count_source'] = 'recorded'
            if name.endswith('Encoder'):
                a, c = amo_counts(SOLVERS[name], n)
                a = (2 * n + 2) * a + 4 * sum(amo_counts(SOLVERS[name], k)[0] for k in range(2, n))
                c = 2 * n + (2 * n + 2) * c + 4 * sum(amo_counts(SOLVERS[name], k)[1] for k in range(2, n))
                for key, value in (('num_vars', n*n+a), ('num_aux_vars', a), ('num_clauses', c)):
                    if row[key] != '':
                        assert int(row[key]) == value, (name, n, key)
                    else:
                        row[key] = value
                        row['count_source'] = 'formula; solve timed out'
            elif name in ('ILP-Gurobi', 'ILP-CPLEX'):
                assert int(row['num_vars']) == n*n and int(row['num_clauses']) == 6*n-6
            rows.append(row)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    table = [r'\begin{tabular}{@{}lrrrrr@{}}', r'\toprule',
             r'Method & $N=20$ & $N=50$ & $N=100$ & $N=150$ & $N=200$ \\ \midrule']
    for name, label in zip(NAMES, LABELS):
        cells = [r for r in rows if r['encoder_name'] == name]
        times = [f"{float(r['total_time']):.3f}" if r['status'] == 'SAT' else 'Timeout' for r in cells]
        table.append(label + ' & ' + ' & '.join(times) + r' \\')
    table.extend((r'\bottomrule', r'\end{tabular}', ''))
    counts = [r'\begin{tabular}{@{}lrrrr@{}}', r'\toprule',
              r'\multirow{2}{*}{Encoding} & \multicolumn{2}{c}{$N=100$} & \multicolumn{2}{c}{$N=200$} \\',
              r'\cmidrule(l){2-3}\cmidrule(l){4-5}',
              r' & Variables & Clauses & Variables & Clauses \\ \midrule']
    for name, label in zip(NAMES[:5], LABELS[:5]):
        values = [f"{int(row[key]):,}" for row in rows
                  if row['encoder_name'] == name and int(row['n']) in (100, 200)
                  for key in ('num_vars', 'num_clauses')]
        counts.append(label + ' & ' + ' & '.join(values) + r' \\')
    counts.extend((r'\bottomrule', r'\end{tabular}', ''))
    outputs = {DATA / 'comparison.csv': buffer.getvalue(),
               ROOT / 'report' / 'tables' / 'common_runtime.tex': '\n'.join(table),
               ROOT / 'report' / 'tables' / 'formula_sizes.tex': '\n'.join(counts)}
    coverage = read_csv(DATA / 'coverage.csv')
    for cell in coverage:
        if cell['encoder_name'] == 'ILP-Gurobi' and int(cell['n']) in SIZES:
            cell['dataset'] = 'nqueens_sat/results/benchmarks/gurobi_corrected_benchmark/summary.csv'
            cell['validation_record'] = 'placement retained in runs.jsonl; independently revalidated'
    coverage_buffer = io.StringIO(newline='')
    coverage_writer = csv.DictWriter(coverage_buffer, fieldnames=list(coverage[0]))
    coverage_writer.writeheader()
    coverage_writer.writerows(coverage)
    outputs[DATA / 'coverage.csv'] = coverage_buffer.getvalue()
    for path, contents in outputs.items():
        if check:
            assert path.read_bytes().decode('utf-8') == contents, f'Stale generated output: {path}'
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding='utf-8', newline='')
    if not check:
        manifest = {'common_sizes': SIZES, 'cells': len(rows), 'repetitions_per_cell': 3,
                    'selection': 'one source session per cell; no pooling', 'sources': {}}
        for session, (_, metadata, retained) in loaded.items():
            manifest['sources'][session] = {'witnesses_retained': retained,
                'source_sha256': metadata.get('source_python_sha256', metadata.get('source_code_sha256')),
                'files_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (DATA / session).iterdir() if p.is_file()}}
        (DATA / 'comparison_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    else:
        manifest = json.loads((DATA / 'comparison_manifest.json').read_text(encoding='utf-8'))
        for session, description in manifest['sources'].items():
            for filename, expected_hash in description['files_sha256'].items():
                assert hashlib.sha256((DATA / session / filename).read_bytes()).hexdigest() == expected_hash
    print(f'Checked {len(rows)} cells; generated comparison CSV and manuscript table' if not check else 'Comparison CSV and manuscript table match validated raw repetitions')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
