from pulp import LpMinimize, LpProblem, LpVariable, constants
from remip_client.solver import ReMIPSolver


async def main():
    # --- Test 1: Non-streaming Success ---
    print("--- Running test: Non-streaming --- ")
    prob = LpProblem("Test_Problem", LpMinimize)
    x = LpVariable("x", lowBound=0)
    prob += x
    prob += x >= 1
    solver = ReMIPSolver(stream=False)
    status = await solver.solve(prob)
    assert status == constants.LpStatusOptimal, (
        f"Expected Optimal, got {constants.LpStatus[prob.status]}"
    )
    assert prob.objective.value == 1.0, (
        f"Expected objective 1.0, got {prob.objective.value}"
    )
    print("✅ Test passed")

    # --- Test 2: Streaming Success ---
    print("--- Running test: Streaming --- ")
    prob_stream = LpProblem("Test_Problem_Stream", LpMinimize)
    x_stream = LpVariable("x_stream", lowBound=0)
    prob_stream += x_stream
    prob_stream += x_stream >= 2
    solver_stream = ReMIPSolver(stream=True)
    status_stream = await solver_stream.solve(prob_stream)
    assert status_stream == constants.LpStatusOptimal, (
        f"Expected Optimal, got {constants.LpStatus[prob_stream.status]}"
    )
    assert prob_stream.objective.value == 2.0, (
        f"Expected objective 2.0, got {prob_stream.objective.value}"
    )
    print("✅ Test passed")

    # --- Test 3: Server Error ---
    print("--- Running test: Server Error --- ")
    prob_error = LpProblem("Error_Problem", LpMinimize)
    y = LpVariable("y", lowBound=0)
    prob_error += y
    solver_error = ReMIPSolver()
    status_error = await solver_error.solve(prob_error)
    assert status_error == constants.LpStatusNotSolved, (
        f"Expected Not Solved, got {constants.LpStatus[prob_error.status]}"
    )
    print("✅ Test passed")


# This is the entry point that will be called from JavaScript
main_coro = main()
