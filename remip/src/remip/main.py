import argparse
import logging
import socket
from typing import AsyncGenerator

import uvicorn
from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware

from .models import MIPProblem, MIPSolution
from .services import MIPSolverService

app = FastAPI(
    title="ReMIP",
    description="A RESTful API for Mixed-Integer Programming (MIP) solvers.",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


def get_solver_service():
    """FastAPI dependency to get a solver service instance."""
    return MIPSolverService()


@app.get("/solver-info")
async def solver_info():
    """Returns information about the solver."""
    return {"solver": "SCIP", "version": "x.y.z"}


@app.post("/solve")
async def solve(
    request: Request,
    problem: MIPProblem,
    service: MIPSolverService = Depends(get_solver_service),
    timeout: float | None = Query(None, ge=0, description="Maximum solver time in seconds"),
    stream: str | None = Query(None, description="Enable SSE streaming of solver events"),
) -> MIPSolution:
    """
    Solves a MIP problem and returns the solution.

    If `stream=sse` is specified, it streams solver events using Server-Sent Events (SSE).
    The client can disconnect at any time, and the solver will be interrupted.
    """

    if stream == "sse":

        async def sse_generator() -> AsyncGenerator[str, None]:
            """Generator that yields SSE events, handling client disconnects."""
            try:
                async for event in service.solve_stream(problem, timeout=timeout):
                    if await request.is_disconnected():
                        print("Client disconnected, interrupting solver.")
                        service.interrupt_solver()
                        break
                    yield event.to_sse()
            except Exception as e:
                print(f"An error occurred during streaming: {e}")

        return StreamingResponse(sse_generator(), media_type="text/event-stream")

    # Default behavior: solve and return the final solution
    solution = await service.solve(problem, timeout=timeout)
    return solution


def main():
    """
    Runs the FastAPI application using uvicorn.
    """
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--host", default="localhost")
    args = parser.parse_args()

    try:
        port = args.port or 8000  # Default port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((args.host, port))
    except OSError:
        if args.port:  # When port argument is specified.
            logging.error(f"The specified port {port} is already in use. Aborting server startup.")
            exit(-1)
        else:
            logging.info(f"Default port {port} is already in use, finding an available port.")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((args.host, 0))
                port = s.getsockname()[1]

    uvicorn.run(app, host=args.host, port=port)


if __name__ == "__main__":
    main()
