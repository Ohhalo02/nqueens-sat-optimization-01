"""Shared benchmark statuses for exact-solver integrations."""

import time


def failure_result(name, n, started, exc=None, integer_variables=False):
    message = str(exc).lower() if exc is not None else ""
    status = "LICENSE_LIMIT" if any(
        token in message for token in ("license", "licence", "promotional", "size limit", "problem size limit")
    ) else "ERROR"
    if exc is None:
        status = "MISSING_DEPENDENCY"
    return {
        "encoder_name": name,
        "status": status,
        "satisfiable": None,
        "solution": None,
        "num_vars": n if integer_variables else n * n,
        "num_clauses": None,
        "num_aux_vars": 0,
        "encoding_time": None,
        "solving_time": None,
        "decode_time": None,
        "total_time": None,
        "wall_total": time.perf_counter() - started,
        "error_type": type(exc).__name__ if exc is not None else "MissingDependency",
    }
