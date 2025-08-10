from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from .models import MIPProblem, MIPSolution
from .services import MIPSolverService

app = FastAPI()
solver_service = MIPSolverService()

@app.post("/solve", response_model=MIPSolution)
async def solve(problem: MIPProblem):
    """
    Solves a MIP problem and returns the solution.
    """
    return await solver_service.solve_problem(problem)

@app.get("/solve-stream")
async def solve_stream(problem: MIPProblem):
    """
    Solves a MIP problem and streams the solver logs.
    """
    return StreamingResponse(solver_service.solve_problem_stream(problem), media_type="text/plain")

@app.get("/solver-info")
async def solver_info():
    """
    Returns information about the solver.
    """
    # In a real implementation, this would come from the service
    return {"solver": "SCIP", "version": "x.y.z"}