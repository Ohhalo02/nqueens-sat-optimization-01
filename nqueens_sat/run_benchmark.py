"""Reproducible, process-isolated N-Queens benchmark.

The historical benchmark_results.csv is deliberately never overwritten. Each invocation
creates a run directory with raw repetitions, a summary, and environment metadata.
"""

import argparse
import csv
import importlib.metadata
import json
import multiprocessing as mp
import os
import pathlib
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from encoders.binomial import BinomialEncoder
from encoders.binary import BinaryEncoder
from encoders.commander import CommanderEncoder
from encoders.sequential import SequentialEncoder
from encoders.product import ProductEncoder
from baselines.ilp_solver import ILPSolver
from baselines.cp_solver import CPSolver
from baselines.gurobi_solver import GurobiSolver
from baselines.cplex_mip_solver import CplexMIPSolver
from baselines.cplex_cp_solver import CplexCPSolver
from utils import validate_solution

SOLVERS = {
    'BinomialEncoder': BinomialEncoder,
    'BinaryEncoder': BinaryEncoder,
    'CommanderEncoder': CommanderEncoder,
    'SequentialEncoder': SequentialEncoder,
    'ProductEncoder': ProductEncoder,
    'ILP-PuLP-CBC': ILPSolver,
    'CP-SAT-ORTools': CPSolver,
    'ILP-Gurobi': GurobiSolver,
    'ILP-CPLEX': CplexMIPSolver,
    'CP-CPLEX': CplexCPSolver,
}
SIZES = (4, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200)
RAW_FIELDS = ('encoder_name', 'n', 'repeat', 'status', 'satisfiable', 'num_vars',
              'num_clauses', 'num_aux_vars', 'encoding_time', 'solving_time',
              'decode_time', 'total_time', 'wall_total', 'process_wall_time',
              'conflicts', 'decisions', 'propagations', 'restarts', 'native_status',
              'error_type')
SUMMARY_FIELDS = ('encoder_name', 'n', 'status', 'n_repeats', 'n_success',
                  'satisfiable', 'num_vars', 'num_clauses', 'num_aux_vars',
                  'encoding_time', 'solving_time', 'decode_time', 'total_time',
                  'wall_total', 'conflicts', 'decisions', 'propagations', 'restarts')
METRICS = ('encoding_time', 'solving_time', 'decode_time', 'total_time',
           'wall_total', 'conflicts', 'decisions', 'propagations', 'restarts')


def _worker(send_end, name, n, time_limit):
    try:
        result = SOLVERS[name]().solve(n, time_limit)
        status = result.get('status', 'ERROR')
        if status == 'SAT' and not validate_solution(result.get('solution'), n):
            status = 'INVALID_SOLUTION'
            result['satisfiable'] = None
        result['status'] = status
        result.pop('solution', None)
        send_end.send(result)
    except BaseException as exc:
        send_end.send({'encoder_name': name, 'status': 'ERROR',
                       'satisfiable': None, 'error_type': type(exc).__name__})
    finally:
        send_end.close()


def run_once(name, n, wall_limit):
    """Terminate a child that exceeds the full-process wall deadline."""
    ctx = mp.get_context('spawn')
    receive_end, send_end = ctx.Pipe(duplex=False)
    process = ctx.Process(target=_worker, args=(send_end, name, n, wall_limit))
    started = time.perf_counter()
    try:
        process.start()
        send_end.close()
        process.join(wall_limit)
        if process.is_alive():
            # CBC may have launched an external executable from the worker.
            # On Windows, terminate its process tree before the Python worker.
            if os.name == 'nt':
                try:
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                   capture_output=True, timeout=5, check=False)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            process.terminate()
            process.join(5)
            if process.is_alive():
                process.kill()
                process.join()
            result = {'encoder_name': name, 'status': 'TIMEOUT', 'satisfiable': None}
        elif receive_end.poll():
            result = receive_end.recv()
        else:
            result = {'encoder_name': name, 'status': 'ERROR', 'satisfiable': None,
                      'error_type': f'WorkerExit{process.exitcode}'}
        result['process_wall_time'] = time.perf_counter() - started
        return result
    finally:
        receive_end.close()
        if process.is_alive():
            process.terminate()
            process.join()


def _scalar_row(name, n, repetition, result):
    stats = result.get('statistics') or {}
    row = {'encoder_name': name, 'n': n, 'repeat': repetition,
           **{key: result.get(key) for key in RAW_FIELDS if key not in ('encoder_name', 'n', 'repeat')}}
    for key in ('conflicts', 'decisions', 'propagations', 'restarts'):
        row[key] = stats.get(key, row.get(key))
    return row


def _summary(name, n, rows, expected_repeats):
    success = [r for r in rows if r['status'] in ('SAT', 'UNSAT')]
    statuses = {r['status'] for r in rows}
    complete = len(rows) == expected_repeats and len(success) == expected_repeats and len(statuses) == 1
    status = success[0]['status'] if complete else 'PARTIAL' if success else rows[-1]['status']
    out = {'encoder_name': name, 'n': n, 'status': status,
           'n_repeats': len(rows), 'n_success': len(success),
           'satisfiable': success[0]['satisfiable'] if complete else None}
    for key in ('num_vars', 'num_clauses', 'num_aux_vars'):
        out[key] = success[0].get(key) if complete else None
    for key in METRICS:
        vals = [float(r[key]) for r in success if r.get(key) not in (None, '')]
        out[key] = statistics.median(vals) if complete and len(vals) == expected_repeats else None
    return out


def _metadata(args, run_id):
    def git(*parts):
        try:
            return subprocess.check_output(['git', *parts], cwd=ROOT, text=True,
                                           stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    versions = {}
    for package in ('python-sat', 'pulp', 'ortools', 'gurobipy', 'docplex', 'cplex',
                    'matplotlib', 'seaborn', 'pandas', 'numpy'):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {'run_id': run_id, 'created_utc': datetime.now(timezone.utc).isoformat(),
            'source_commit': git('rev-parse', 'HEAD'),
            'source_dirty': bool(git('status', '--porcelain')),
            'python': sys.version, 'python_executable_name': pathlib.Path(sys.executable).name,
            'platform': platform.platform(), 'processor': platform.processor(),
            'logical_cpus': os.cpu_count(), 'package_versions': versions,
            'solver_workers': 1, 'selected_solvers': args.solvers,
            'selected_sizes': args.sizes, 'requested_repeats': args.repeats,
            'wall_limit_seconds_per_repeat': args.wall_limit,
            'timing_definition': {'total_time': 'model construction + solver invocation',
                                  'wall_total': 'inside solve(), including solution extraction',
                                  'process_wall_time': 'parent clock, including worker startup and validation'},
            'summary_statistic': 'median of complete repetitions'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solvers', nargs='+', choices=tuple(SOLVERS), default=list(SOLVERS))
    parser.add_argument('--sizes', nargs='+', type=int, default=list(SIZES))
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--wall-limit', type=float, default=300)
    parser.add_argument('--output', type=pathlib.Path)
    args = parser.parse_args(argv)
    if args.repeats < 1 or args.wall_limit <= 0 or any(n < 1 for n in args.sizes):
        parser.error('repeats, wall-limit, and sizes must be positive')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = args.output or HERE / 'results' / 'runs' / run_id
    metadata = _metadata(args, run_id)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    with (output / 'raw.csv').open('w', newline='', encoding='utf-8') as raw_file, \
         (output / 'summary.csv').open('w', newline='', encoding='utf-8') as summary_file:
        raw_writer = csv.DictWriter(raw_file, fieldnames=RAW_FIELDS)
        summary_writer = csv.DictWriter(summary_file, fieldnames=SUMMARY_FIELDS)
        raw_writer.writeheader()
        summary_writer.writeheader()
        for name in args.solvers:
            for n in args.sizes:
                rows = []
                for repetition in range(1, args.repeats + 1):
                    result = run_once(name, n, args.wall_limit)
                    row = _scalar_row(name, n, repetition, result)
                    raw_writer.writerow(row)
                    raw_file.flush()
                    rows.append(row)
                    print(f'{name} N={n} repeat={repetition}: {row["status"]}', flush=True)
                summary_writer.writerow(_summary(name, n, rows, args.repeats))
                summary_file.flush()
    print(f'Results: {output.resolve()}')
    return output


if __name__ == '__main__':
    mp.freeze_support()
    main()
