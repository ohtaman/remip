from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Parameters(BaseModel):
    name: str
    sense: int
    status: int
    sol_status: int


class ObjectiveCoefficient(BaseModel):
    name: str
    value: float


class Objective(BaseModel):
    name: Optional[str] = None
    coefficients: List[ObjectiveCoefficient]


class Variable(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    category: str = Field(..., alias="cat")
    lower_bound: Optional[float] = Field(None, alias="lowBound")
    upper_bound: Optional[float] = Field(None, alias="upBound")
    value: Optional[float] = Field(None, alias="varValue")
    reduced_cost: Optional[float] = Field(None, alias="dj")


class Constraint(BaseModel):
    name: Optional[str] = None
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
    diagnostics: Optional["Diagnostics"] = None


class ViolatedConstraint(BaseModel):
    name: str
    violation_amount: float
    left_hand_side: float
    right_hand_side: float
    sense: str


class Diagnostics(BaseModel):
    violated_constraints: List[ViolatedConstraint] = []
    irreducible_infeasible_set: List[str] = []
    dual_values: Dict[str, float] = {}


# SSE Event Models
class LogEvent(BaseModel):
    type: Literal["log"] = "log"
    timestamp: str
    level: str
    stage: str
    message: str
    sequence: int


class MetricEvent(BaseModel):
    type: Literal["metric"] = "metric"
    timestamp: str
    objective_value: float
    gap: float
    iteration: int
    sequence: int


class ResultEvent(BaseModel):
    type: Literal["result"] = "result"
    timestamp: str
    solution: MIPSolution
    runtime_milliseconds: int
    sequence: int


class EndEvent(BaseModel):
    type: Literal["end"] = "end"
    success: bool


SolverEvent = Union[LogEvent, MetricEvent, ResultEvent, EndEvent]
