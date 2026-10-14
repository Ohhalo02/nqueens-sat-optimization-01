"""Regression checks for solver integration and reproducible artifacts."""

import contextlib
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault('MPLBACKEND', 'Agg')

import matplotlib.pyplot as plt

from artifacts import text_sha256
from baselines.cplex_cp_solver import CplexCPSolver
from baselines.ilp_solver import ILPSolver
from run_benchmark import _scalar_row, _summary, run_once
from utils import validate_solution
import prepare_comparison
import package_report
import visualize

ROOT = Path(__file__).resolve().parent.parent


class SolverRegressionTests(unittest.TestCase):
    def test_cbc_works_from_space_and_unicode_paths(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory(prefix='N Queens thử nghiệm ') as directory:
            try:
                os.chdir(directory)
                for n in (2, 4):
                    result = ILPSolver().solve(n, time_limit=5)
                    self.assertEqual(result['status'], 'UNSAT' if n == 2 else 'SAT', result)
                    if n == 4:
                        self.assertTrue(validate_solution(result['solution'], n))
                self.assertEqual(list(Path('.').glob('.cbc-*')), [])
            finally:
                os.chdir(original)

    def test_cp_optimizer_distinguishes_stop_causes(self):
        for native, stop, has_solution, expected in (
            ('Unknown', 'SearchStoppedByLimit', False, 'TIMEOUT'),
            ('Unknown', 'SearchStoppedByAbort', False, 'UNKNOWN'),
            ('Infeasible', 'SearchCompleted', False, 'UNSAT'),
            ('Feasible', 'SearchStoppedByLimit', True, 'SAT'),
        ):
            with self.subTest(expected=expected):
                model = MagicMock()
                model.integer_var_list.return_value = [0]
                solution = model.solve.return_value
                solution.is_solution.return_value = has_solution
                solution.get_solve_status.return_value = native
                solution.get_stop_cause.return_value = stop
                solution.__getitem__.return_value = 0
                with patch('baselines.cplex_cp_solver.CpoModel', return_value=model):
                    result = CplexCPSolver().solve(1, 0.01)
                self.assertEqual(result['status'], expected)
                self.assertEqual(result['stop_cause'], stop)

    def test_process_deadline_is_not_unsat(self):
        result = run_once('BinaryEncoder', 200, 0.05)
        self.assertEqual(result['status'], 'TIMEOUT')
        self.assertIsNone(result['satisfiable'])

    def test_partial_repetitions_have_no_runtime_median(self):
        rows = [dict(status='SAT', satisfiable=True, total_time=1.0),
                dict(status='TIMEOUT', satisfiable=None),
                dict(status='SAT', satisfiable=True, total_time=3.0)]
        result = _summary('BinaryEncoder', 4, rows, 3)
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertIsNone(result['total_time'])

    def test_error_and_stop_details_survive_csv_projection(self):
        details = {'status': 'ERROR', 'error_code': 10022,
                   'error_hint': 'Check network access to the license server.',
                   'stop_cause': 'SearchStoppedByLimit'}
        result = _scalar_row('ILP-Gurobi', 4, 1, details)
        for key, value in details.items():
            self.assertEqual(result[key], value)


class ArtifactRegressionTests(unittest.TestCase):
    def test_report_archive_survives_checkout_and_detects_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / 'report'
            shutil.copytree(ROOT / 'report', report)
            os.utime(report / 'main.pdf', None)
            archive = root / 'report.zip'
            with patch.object(package_report, 'REPORT', report), \
                 contextlib.redirect_stdout(io.StringIO()):
                package_report.package(archive)
                for path in report.rglob('*'):
                    if path.suffix in package_report.TEXT_SUFFIXES:
                        text = path.read_text(encoding='utf-8')
                        path.write_bytes(text.replace('\n', '\r\n').encode('utf-8'))
                # Simulate checkout mtimes: text can be newer than the PDF.
                os.utime(report / 'main.pdf', (1, 1))
                package_report.package(archive, check=True)
                with (report / 'main.tex').open('a', encoding='utf-8') as stream:
                    stream.write('\n% Source changed after packaging\n')
                with self.assertRaisesRegex(ValueError, 'manifest differs'):
                    package_report.package(archive, check=True)

    def test_text_hash_ignores_only_newline_representation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.csv'
            path.write_bytes(b'n,time\n4,0.5\n')
            expected = text_sha256(path)
            path.write_bytes(b'n,time\r\n4,0.5\r\n')
            self.assertEqual(text_sha256(path), expected)
            path.write_bytes(b'n,time\n4,0.6\n')
            self.assertNotEqual(text_sha256(path), expected)

    def test_full_comparison_checks_lf_and_crlf_checkouts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / 'nqueens_sat' / 'results' / 'benchmarks'
            shutil.copytree(ROOT / 'nqueens_sat' / 'results' / 'benchmarks', data)
            shutil.copytree(ROOT / 'report' / 'tables', root / 'report' / 'tables')
            for newline in (b'\n', b'\r\n'):
                for path in root.rglob('*'):
                    if path.is_file():
                        path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', newline))
                with patch.object(prepare_comparison, 'ROOT', root), \
                     patch.object(prepare_comparison, 'DATA', data), \
                     contextlib.redirect_stdout(io.StringIO()):
                    prepare_comparison.build(check=True)

    def test_custom_figure_output_does_not_touch_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            custom = root / 'custom'
            report = root / 'report'
            fig, axis = plt.subplots()
            axis.plot([1, 2], [2, 3])
            try:
                with patch.object(visualize, 'DEFAULT_SAVE_DIRS', [str(report)]):
                    visualize._save_figure(fig, 'sample', save_dir=custom)
                self.assertTrue((custom / 'sample.pdf').is_file())
                self.assertTrue((custom / 'sample.png').is_file())
                self.assertFalse(report.exists())
            finally:
                plt.close(fig)

    def test_alternate_csv_requires_explicit_output(self):
        with self.assertRaisesRegex(ValueError, '--output-dir'):
            visualize.generate_all_plots(ROOT / 'nqueens_sat' / 'results' / 'benchmark_results.csv')


if __name__ == '__main__':
    unittest.main()
