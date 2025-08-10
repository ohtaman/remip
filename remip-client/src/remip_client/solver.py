import json
import sys

from pulp import LpProblem, LpSolver, constants

is_pyodide = "pyodide" in sys.modules

if is_pyodide:
    import pyodide.http
else:
    import httpx


class MipApiSolver(LpSolver):
    """
    A PuLP solver that uses the MIP Solver API.
    Works in both CPython and Pyodide environments.
    """

    def __init__(self, base_url="http://localhost:8000", transport=None, **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.transport = transport
        self.client = None

    async def __aenter__(self):
        if not is_pyodide:
            self.client = httpx.AsyncClient(transport=self.transport)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def actualSolve(self, lp: LpProblem):
        raise NotImplementedError(
            "This solver is async-only. Please call the .solve() method instead."
        )

    async def solve(self, lp: LpProblem):
        """
        Solves the problem by sending it to the MIP Solver API.
        """
        problem_dict = lp.toDict()

        try:
            if is_pyodide:
                response = await pyodide.http.pyfetch(
                    f"{self.base_url}/solve",
                    method="POST",
                    headers={"Content-Type": "application/json"},
                    body=json.dumps(problem_dict),
                )
                if response.status < 200 or response.status >= 300:
                    print(f"Error from API: {await response.string()}")
                    lp.status = constants.LpStatusInfeasible
                    return lp.status
                solution = await response.json()
            else:
                response = await self.client.post(
                    f"{self.base_url}/solve", json=problem_dict
                )
                response.raise_for_status()
                solution = response.json()

        except Exception as e:
            print(f"Could not connect to API or other error occurred: {e}")
            lp.status = constants.LpStatusNotSolved
            return lp.status

        status_map = {
            "optimal": constants.LpStatusOptimal,
            "infeasible": constants.LpStatusInfeasible,
            "unbounded": constants.LpStatusUnbounded,
            "not solved": constants.LpStatusNotSolved,
            "timelimit": constants.LpStatusNotSolved,
        }
        lp.status = status_map.get(solution["status"], constants.LpStatusUndefined)
        lp.objective.value = solution["objective_value"]

        for var in lp.variables():
            if var.name in solution["variables"]:
                var.varValue = solution["variables"][var.name]

        return lp.status