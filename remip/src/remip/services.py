from typing import AsyncGenerator, Optional

from .models import MIPProblem, MIPSolution, SolverEvent
from .solvers.scip_wrapper import ScipSolverWrapper


class MIPSolverService:
    """
    Service to handle the logic of solving MIP problems.
    """

    def __init__(self):
        self.solver = ScipSolverWrapper()

    async def solve(self, problem_data: MIPProblem, timeout: Optional[float] = None) -> MIPSolution:
        """
        Solves the problem and returns the final result.
        """
        return await self.solver.solve(problem_data, timeout=timeout)

    async def solve_stream(
        self, problem_data: MIPProblem, timeout: Optional[float] = None
    ) -> AsyncGenerator[SolverEvent, None]:
        """
        Solves the problem and yields solver events.
        """
        async for event in self.solver.solve_and_stream_events(problem_data, timeout=timeout):
            yield event
