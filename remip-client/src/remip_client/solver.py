from pulp import LpSolver, LpProblem, constants
import httpx

class MipApiSolver(LpSolver):
    """
    A PuLP solver that uses the MIP Solver API.
    """

    def __init__(self, base_url="http://localhost:8000", **kwargs):
        """
        Initializes the solver.

        :param base_url: The base URL of the MIP Solver API.
        """
        super().__init__(**kwargs)
        self.base_url = base_url
        self.client = httpx.Client()

    def available(self):
        """
        Checks if the API is available.
        """
        try:
            response = self.client.get(f"{self.base_url}/solver-info")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def actualSolve(self, lp: LpProblem):
        """
        Solves the problem by sending it to the MIP Solver API.
        """
        # 1. Convert the problem to a dictionary
        problem_dict = lp.toDict()

        # 2. Send the problem to the API
        try:
            response = self.client.post(f"{self.base_url}/solve", json=problem_dict, timeout=self.timeLimit)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Handle API errors gracefully
            print(f"Error from API: {e.response.text}")
            lp.status = constants.LpStatusInfeasible # Or another appropriate status
            return lp.status
        except httpx.RequestError as e:
            print(f"Could not connect to API: {e}")
            lp.status = constants.LpStatusNotSolved
            return lp.status

        # 3. Parse the solution
        solution = response.json()

        # 4. Update the LpProblem object with the solution
        status_map = {
            "optimal": constants.LpStatusOptimal,
            "infeasible": constants.LpStatusInfeasible,
            "unbounded": constants.LpStatusUnbounded,
            "not solved": constants.LpStatusNotSolved,
            "timelimit": constants.LpStatusNotSolved, # Or a custom status
        }
        lp.status = status_map.get(solution['status'], constants.LpStatusUndefined)
        lp.objective.value = solution['objective_value']

        for var in lp.variables():
            if var.name in solution['variables']:
                var.varValue = solution['variables'][var.name]

        return lp.status