from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from .models import MIPProblem, MIPSolution
from .services import MIPSolverService

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


# Serve static files from the remip-client directory
static_dir = Path(__file__).parent.parent.parent / "remip-client"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


def main():
    """
    Runs the FastAPI application using uvicorn.
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
