import json
from pulp import LpProblem, constants
from pulp.apis import LpSolver
from .environment import get_environment

ENV = get_environment()

# Create a reverse mapping from status string to integer code, as LpStatus is {code: str}
STATUS_MAP = {v.lower(): k for k, v in constants.LpStatus.items()}

# Conditionally set the base class to inherit from LpSolver only in CPython
BaseSolver = LpSolver if ENV == "cpython" else object


class AtributeDict(dict):
    def __setattr__(self, name: str, value: any) -> None:
        self[name] = value

    def __getattr__(self, name: str) -> any:
        return self[name]


class ReMIPSolver(BaseSolver):
    """
    A PuLP solver that sends problems to a remote ReMIP server.
    It uses the standard PuLP API in CPython, but a custom async API in Pyodide.
    """

    def __init__(
        self,
        url: str = "http://localhost:8000",
        stream: bool = False,
        timeout: int = 60,
        env=ENV,
        **kwargs,
    ):
        if env == "cpython":
            super().__init__(**kwargs)

        self.env = env
        self.url = url
        self.stream = stream
        self.timeout = timeout
        self.solution = None

        if env in ("pyodide-node", "pyodide-browser"):
            from .http_client import PyodideHttpClient

            self.http_client = PyodideHttpClient(base_url=self.url, stream=self.stream)
        else:
            from .http_client import RequestsHttpClient

            self.http_client = RequestsHttpClient(base_url=self.url, stream=self.stream)

    def _parse_solution(self, lp: LpProblem, solution: dict):
        """Helper function to update the LpProblem with the solution."""
        status_str = solution.get("status", "Not Solved").lower()
        lp.status = STATUS_MAP.get(status_str, constants.LpStatusNotSolved)
        lp.objective.value = solution.get("objective_value")

        variables = solution.get("variables") or {}
        reduced_costs = solution.get("reduced_costs") or {}
        for var in lp.variables():
            if var.name in variables:
                var.varValue = variables[var.name]
            if var.name in reduced_costs:
                var.dj = reduced_costs[var.name]

        slacks = solution.get("slacks") or {}
        duals = solution.get("duals") or {}
        for name, constraint in lp.constraints.items():
            if name in duals:
                constraint.pi = duals[name]
            if name in slacks:
                constraint.slack = slacks[name]

    def actualSolve(self, lp: LpProblem) -> int:
        """Standard PuLP entry point for CPython."""
        if self.env != "cpython":
            raise NotImplementedError(
                "actualSolve is only for the CPython environment. Use the async solve() method in Pyodide."
            )

        try:
            response = self.http_client.solve(lp.toDict(), timeout=self.timeout)

            if self.stream:
                solution = None
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        # SSE format is "data: {JSON_STRING}"
                        data_str = line.decode("utf-8").split("data: ")[1]
                        data = json.loads(data_str)
                        if "solution" in data:
                            solution = data["solution"]
                    except (json.JSONDecodeError, IndexError):
                        # Ignore lines that are not valid SSE JSON
                        continue
            else:
                solution = response.json()

            self.solution = AtributeDict(solution)
            self._parse_solution(lp, solution)
            return lp.status
        except Exception:
            lp.status = constants.LpStatusNotSolved
            return lp.status

    async def solve(self, lp: LpProblem) -> int:
        """Asynchronous entry point for the Pyodide environment."""
        if self.env == "cpython":
            raise NotImplementedError(
                "Use lp.solve(solver) in the CPython environment."
            )

        try:
            response = await self.http_client.solve(lp.toDict(), timeout=self.timeout)

            if self.stream:
                solution = None
                async for line in response.iter_lines():
                    if line:
                        try:
                            # SSE format is "data: {JSON_STRING}"
                            data_str = line.decode("utf-8").split("data: ")[1]
                            solution = json.loads(data_str)["solution"]
                        except (json.JSONDecodeError, IndexError):
                            # Ignore lines that are not valid SSE JSON
                            continue
            else:
                solution = await response.json()

            self.solution = AtributeDict(solution)
            self._parse_solution(lp, solution)
            return lp.status
        except Exception:
            lp.status = constants.LpStatusNotSolved
            return lp.status
