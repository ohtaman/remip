from remip_client.http_client import PyodideHttpClient, RequestsHttpClient
from remip_client.solver import ReMIPSolver


def test_solver_instantiates_requests_client():
    """Verify that ReMIPSolver instantiates RequestsHttpClient in a CPython environment."""
    solver = ReMIPSolver(env="cpython")
    assert isinstance(solver.http_client, RequestsHttpClient)


def test_solver_instantiates_pyodide_client():
    """Verify that ReMIPSolver instantiates PyodideHttpClient in a Pyodide/Node environment."""
    solver = ReMIPSolver(env="pyodide-node")
    assert isinstance(solver.http_client, PyodideHttpClient)


def test_solver_instantiates_pyodide_client_for_browser():
    """Verify that ReMIPSolver also instantiates PyodideHttpClient for the browser environment."""
    solver = ReMIPSolver(env="pyodide-browser")
    assert isinstance(solver.http_client, PyodideHttpClient)
