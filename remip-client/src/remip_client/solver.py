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

    def __init__(
        self, base_url="http://localhost:8000", transport=None, stream=True, **kwargs
    ):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.transport = transport
        self.stream = stream
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
        Solves the problem by sending it to the MIP Solver API.
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
        Solves the problem by sending it to the MIP Solver API.
        """
        problem_dict = lp.toDict()
        solution_json = None

        try:
            if not self.stream:
                # Non-streaming case
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
                    solution_json = await response.string()
                else:  # httpx
                    response = await self.client.post(
                        f"{self.base_url}/solve",
                        json=problem_dict,
                        timeout=None,
                    )
                    response.raise_for_status()
                    solution_json = response.text
            else:
                # Streaming case
                if is_pyodide:
                    response = await pyodide.http.pyfetch(
                        f"{self.base_url}/solve?stream=sse",
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

                    all_events_raw = buffer.decode("utf-8").strip().split("\n\n")
                    for event_raw in all_events_raw:
                        lines = event_raw.split("\n")
                        event_type = ""
                        event_data = ""
                        for line in lines:
                            if line.startswith("event: "):
                                event_type = line[len("event: ") :]
                            elif line.startswith("data: "):
                                event_data = line[len("data: ") :]

                        if event_type == "result":
                            data = json.loads(event_data)
                            solution_json = json.dumps(data.get("solution"))
                        elif event_type == "log":
                            data = json.loads(event_data)
                            print(
                                f"[{data.get('timestamp')}] [{data.get('level')}] {data.get('message')}"
                            )
                        elif event_type == "metric":
                            data = json.loads(event_data)
                            print(
                                f"[{data.get('timestamp')}] Iter: {data.get('iteration')}, "
                                f"Obj: {data.get('objective_value')}, Gap: {data.get('gap')}"
                            )

                else:  # httpx
                    current_event = {}
                    async with self.client.stream(
                        "POST",
                        f"{self.base_url}/solve?stream=sse",
                        json=problem_dict,
                        timeout=None,
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line:  # End of an event
                                if current_event.get("type") == "result":
                                    data = json.loads(current_event.get("data", "{}"))
                                    solution_json = json.dumps(data.get("solution"))
                                elif current_event.get("type") == "log":
                                    data = json.loads(current_event.get("data", "{}"))
                                    print(
                                        f"[{data.get('timestamp')}] [{data.get('level')}] {data.get('message')}"
                                    )
                                elif current_event.get("type") == "metric":
                                    data = json.loads(current_event.get("data", "{}"))
                                    print(
                                        f"[{data.get('timestamp')}] Iter: {data.get('iteration')}, "
                                        f"Obj: {data.get('objective_value')}, Gap: {data.get('gap')}"
                                    )
                                current_event = {}
                                continue

                            if line.startswith("event: "):
                                current_event["type"] = line[len("event: ") :]
                            elif line.startswith("data: "):
                                current_event["data"] = line[len("data: ") :]
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
