import json

import requests
from pulp import LpProblem, LpSolver, constants


class ReMIPSolver(LpSolver):
    """
    A PuLP solver that uses the MIP Solver API.
    Works in both CPython and Pyodide environments.
    """

    def __init__(self, base_url="http://localhost:8000", stream=True, **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.stream = stream

    def actualSolve(self, lp: LpProblem) -> int:
        """
        Solves the problem by sending it to the MIP Solver API.
        """
        return self.solve(lp)

    def solve(self, lp: LpProblem) -> int:
        """
        Solves the problem by sending it to the MIP Solver API.
        """
        problem_dict = lp.toDict()
        solution = None

        try:
            if not self.stream:
                # Non-streaming case
                response = requests.post(
                    f"{self.base_url}/solve",
                    json=problem_dict,
                    timeout=None,
                )
                response.raise_for_status()
                solution = response.json()
            else:
                # Streaming case
                response = requests.post(
                    f"{self.base_url}/solve?stream=sse",
                    json=problem_dict,
                    timeout=None,
                    stream=True,
                )
                response.raise_for_status()
                current_event = None
                for line in response.iter_lines():
                    line = line.decode("utf-8")
                    if not line:  # Skip empty lines
                        continue
                    if line.startswith("event: "):
                        current_event = line[7:]  # Remove "event: " prefix
                    elif line.startswith("data: "):
                        if current_event is None:
                            continue
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        print("---- >> data row <<--", current_event)
                        match current_event:
                            case "result":
                                # Handle both cases: data contains solution directly or nested in solution field
                                if "solution" in data:
                                    solution = data["solution"]
                                else:
                                    solution = data
                            case "log":
                                print(
                                    f"[{data.get('timestamp')}] [{data.get('level')}] {data.get('message')}"
                                )
                            case "metric":
                                print(
                                    f"[{data.get('timestamp')}] Iter: {data.get('iteration')}, "
                                    f"Obj: {data.get('objective_value')}, Gap: {data.get('gap')}"
                                )
                            case _:
                                # ignore unknown event
                                continue
        except requests.exceptions.RequestException as e:
            print(f"Could not connect to API: {e}")
            lp.status = constants.LpStatusNotSolved
            return lp.status
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            lp.status = constants.LpStatusNotSolved
            return lp.status

        if solution is None:
            print("Error: Did not receive solution from server.")
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
        if solution.get("objective_value") is not None:
            lp.objective.value = solution["objective_value"]

        if lp.status == constants.LpStatusOptimal:
            for var in lp.variables():
                if var.name in solution["variables"]:
                    var.varValue = solution["variables"][var.name]

        return lp.status
