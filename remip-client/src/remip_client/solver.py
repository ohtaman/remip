import asyncio
import json
import sys

from pulp import LpProblem, LpSolver, constants

is_pyodide = "pyodide" in sys.modules

if is_pyodide:
    import pyodide.http
else:
    import httpx


class ReMIPSolver(LpSolver):
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

    def actualSolve(self, lp: LpProblem) -> int:
        """
        Jupyter-safe: wait for the coroutine even when an event loop is already running.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop → create one
            return asyncio.run(self.solve(lp))
        else:
            # Running loop (Jupyter) → allow nested run
            try:
                import nest_asyncio

                nest_asyncio.apply(loop)
            except Exception:
                pass  # if not available, fall back to thread strategy or raise
            return loop.run_until_complete(self.solve(lp))

    async def solve(self, lp: LpProblem) -> int:
        """
        Solves the problem by sending it to the MIP Solver API and streaming logs.
        """
        problem_dict = lp.toDict()
        solution_json = None

        try:
            if is_pyodide:
                response = await pyodide.http.pyfetch(
                    f"{self.base_url}/solve-stream",
                    method="POST",
                    headers={"Content-Type": "application/json"},
                    body=json.dumps(problem_dict),
                    stream=True,
                )
                if response.status < 200 or response.status >= 300:
                    print(f"Error from API: {await response.string()}")
                    lp.status = constants.LpStatusInfeasible
                    return lp.status

                # Read the streaming body
                reader = response.body.getReader()
                buffer = b""
                while True:
                    chunk = await reader.read()
                    if chunk.done:
                        break
                    buffer += chunk.value

                all_lines = buffer.decode("utf-8").splitlines()
                for line in all_lines:
                    if line.startswith("LOG: "):
                        print(line[5:])
                    elif line.startswith("RESULT: "):
                        solution_json = line[8:]

            else:  # httpx
                async with self.client.stream(
                    "POST",
                    f"{self.base_url}/solve-stream",
                    json=problem_dict,
                    timeout=None,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("LOG: "):
                            print(line[5:])
                        elif line.startswith("RESULT: "):
                            solution_json = line[8:]

        except Exception as e:
            print(f"Could not connect to API or other error occurred: {e}")
            lp.status = constants.LpStatusNotSolved
            return lp.status

        if solution_json is None:
            print("Error: Did not receive solution from server.")
            lp.status = constants.LpStatusNotSolved
            return lp.status

        solution = json.loads(solution_json)

        status_map = {
            "optimal": constants.LpStatusOptimal,
            "infeasible": constants.LpStatusInfeasible,
            "unbounded": constants.LpStatusUnbounded,
            "not solved": constants.LpStatusNotSolved,
            "timelimit": constants.LpStatusNotSolved,
        }
        lp.status = status_map.get(solution["status"], constants.LpStatusUndefined)
        if solution.get("objective_value") is not None:
            lp.objective.value = solution["objective_value"]

        if lp.status == constants.LpStatusOptimal:
            for var in lp.variables():
                if var.name in solution["variables"]:
                    var.varValue = solution["variables"][var.name]

        return lp.status
