from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Parameters(BaseModel):
    name: str
    sense: int
    status: int
    sol_status: int

class ObjectiveCoefficient(BaseModel):
    name: str
    value: float

class Objective(BaseModel):
    name: str
    coefficients: List[ObjectiveCoefficient]

class Variable(BaseModel):
    name: str
    cat: str
    lowBound: Optional[float] = None
    upBound: Optional[float] = None
    varValue: Optional[float] = None
    dj: Optional[float] = None

class Constraint(BaseModel):
    name: str
    sense: int
    coefficients: List[ObjectiveCoefficient]
    pi: Optional[float] = None
    constant: Optional[float] = None

class MIPProblem(BaseModel):
    parameters: Parameters
    objective: Objective
    variables: List[Variable]
    constraints: List[Constraint]
    sos1: List[Dict] = []
    sos2: List[Dict] = []
    solver_options: Optional[Dict[str, Any]] = None

class MIPSolution(BaseModel):
    """
    Represents the solution of a MIP problem.
    """
    name: str
    status: str
    objective_value: Optional[float]
    variables: Dict[str, float]
