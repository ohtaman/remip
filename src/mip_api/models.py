from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ObjectiveCoefficient(BaseModel):
    name: str
    value: float

class Objective(BaseModel):
    name: str
    coefficients: List[ObjectiveCoefficient]

class Variable(BaseModel):
    name: str
    lowBound: Optional[float] = None
    upBound: Optional[float] = None
    cat: str

class MIPProblem(BaseModel):
    """
    Represents a Mixed-Integer Programming problem based on PuLP's to_dict() structure.
    """
    name: str
    sense: int
    objective: Objective
    constraints: List[Dict] # Keeping constraints as Dict for now to avoid too much complexity
    variables: Dict[str, Variable]
    solver_options: Optional[Dict[str, Any]] = None # For solver-specific kwargs

class MIPSolution(BaseModel):
    """
    Represents the solution of a MIP problem.
    """
    name: str
    status: str
    objective_value: float
    variables: Dict[str, float]