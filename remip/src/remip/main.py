import argparse
import logging
import socket
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse

from .models import MIPProblem
from .services import MIPSolverService

logger = logging.getLogger(__name__)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


def get_solver_service():
    return MIPSolverService()


@app.get("/health")
async def health():
    return True


@app.post("/solve")
async def solve(
    request: Request,
    problem: MIPProblem,
    service: MIPSolverService = Depends(get_solver_service),
    timeout: Optional[float] = Query(None, ge=0, description="Maximum solver time in seconds"),
):
    """
    Solves a MIP problem and returns the solution.
    If the 'stream' query parameter is set to 'sse' or the 'Accept' header is 'text/event-stream',
    it streams solver events using Server-Sent Events (SSE).
    """
    stream_param = request.query_params.get("stream", "").lower()
    accept_header = request.headers.get("accept", "").lower()

    is_streaming_request = "sse" in stream_param or "text/event-stream" in accept_header

    if is_streaming_request:

        async def event_generator():
            async for event in service.solve_stream(problem, timeout=timeout):
                yield f"event: {event.type}\n"
                yield f"data: {event.model_dump_json()}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    else:
        solution = await service.solve(problem, timeout=timeout)
        return solution


@app.get("/solver-info")
async def solver_info():
    """
    Returns information about the solver.
    """
    return {"solver": "SCIP", "version": "x.y.z"}


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
            logger.error(f"The specified port {port} is already in use. Aborting server startup.")
            exit(-1)
        else:
            logger.info(f"Default port {port} is already in use, finding an available port.")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((args.host, 0))
                port = s.getsockname()[1]

    uvicorn.run(app, host=args.host, port=port)


if __name__ == "__main__":
    main()
