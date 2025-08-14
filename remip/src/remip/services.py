from typing import AsyncGenerator

from .models import MIPProblem, MIPSolution
from .solvers.scip_wrapper import ScipSolverWrapper


class MIPSolverService:
    """
    Service to handle the logic of solving MIP problems.
    """

    def __init__(self):
        self.solver = ScipSolverWrapper()

    async def solve_problem(self, problem_data: MIPProblem) -> MIPSolution:
        """
        Solves the problem and returns the final result.
        """
        return await self.solver.solve(problem_data)

    async def solve_problem_stream(self, problem_data: MIPProblem) -> AsyncGenerator[str, None]:
        """
        Solves the problem and yields log lines.
        """
        async for log_line in self.solver.solve_and_stream_logs(problem_data):
            yield log_line