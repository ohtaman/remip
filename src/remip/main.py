from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from .models import MIPProblem, MIPSolution
from .services import MIPSolverService

app = FastAPI()

def get_solver_service():
    return MIPSolverService()

@app.post("/solve", response_model=MIPSolution)
async def solve(problem: MIPProblem, service: MIPSolverService = Depends(get_solver_service)):
    """
    Solves a MIP problem and returns the solution.
    """
    return await service.solve_problem(problem)

@app.post("/solve-stream")
async def solve_stream(problem: MIPProblem, service: MIPSolverService = Depends(get_solver_service)):
    """
    Solves a MIP problem and streams the solver logs.
    """
    return StreamingResponse(service.solve_problem_stream(problem), media_type="text/plain")

@app.get("/solver-info")
async def solver_info():
    """
    Returns information about the solver.
    """
    return {"solver": "SCIP", "version": "x.y.z"}
