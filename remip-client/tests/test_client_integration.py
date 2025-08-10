import subprocess
import time

import pytest
from pulp import LpMaximize, LpProblem, LpVariable
from remip_client.solver import MipApiSolver


# A fixture to run the server for the duration of the test session
@pytest.fixture(scope="session")
def live_server():
    # Command to start the server
    # Note: Using 127.0.0.1 to be explicit
    command = ["uv", "run", "uvicorn", "remip.main:app", "--host", "127.0.0.1", "--port", "8000"]
    
    # Start the server as a background process
    server_process = subprocess.Popen(command)
    
    # Give the server a moment to start up
    time.sleep(3)
    
    # Yield the server URL to the tests
    yield "http://127.0.0.1:8000"
    
    # Teardown: stop the server process after tests are done
    server_process.terminate()
    server_process.wait()

@pytest.mark.asyncio
async def test_client_solve(live_server):
    """
    Tests the full client-server interaction in a CPython environment.
    """
    # 1. Define a problem (same as the pyodide test)
    prob = LpProblem("test_problem_cpython", LpMaximize)
    x = LpVariable("x", 0, 1, cat='Binary')
    y = LpVariable("y", 0, 1, cat='Binary')
    prob += x + y, "objective"
    prob += 2*x + y <= 2, "constraint1"

    # 2. Initialize the remote solver, pointing to the live server
    # The solver needs to be used in an async context
    async with MipApiSolver(base_url=live_server) as solver:
        # 3. Solve the problem
        # We need to call the async solve method directly
        status = await solver.solve(prob)

    # 4. Check the results
    assert status == 1 # LpStatusOptimal
    assert prob.status == 1 # LpStatusOptimal
    assert x.varValue == 1.0
    assert y.varValue == 0.0
