from __future__ import annotations

from datetime import datetime
from typing import Annotated, TYPE_CHECKING, Optional

from graphql import GraphQLError
from strawberry.scalars import JSON
import strawberry
from strawberry import relay

from api_graphql.types.enums import MixSessionStatusEnum

from api_graphql.types.feedback import Feedback
from models import MixSession

if TYPE_CHECKING:
  from api_graphql.types.formula import FormulaType
  from api_graphql.types.production_order import ProductionOrderType

@strawberry.type
class MixSessionType(relay.Node):
  id: relay.NodeID[str]
  session_number: str
  status: MixSessionStatusEnum
  batch_code: str | None
  recipe_snapshot: JSON | None
  total_volume_ml: float | None
  total_weight_g: float | None
  mixed_at: datetime | None
  formula_name_snapshot: str | None
  created_at: datetime
  updated_at: datetime
  
  _model: strawberry.Private[MixSession]
  
  @classmethod
  def from_model(cls, b: MixSession) -> "MixSessionType":
    return cls(
      id=b.id,
      session_number=b.session_number,
      status=MixSessionStatusEnum[b.status.name],
      batch_code=b.batch_code,
      recipe_snapshot=b.recipe_snapshot,
      total_volume_ml=b.total_volume_ml,
      total_weight_g=b.total_weight_g,
      mixed_at=b.mixed_at,
      formula_name_snapshot=b.formula_name_snapshot,
      created_at=b.created_at,
      updated_at=b.updated_at,
      _model=b,
    )
    
  @strawberry.field
  def formula(self) -> Annotated["FormulaType", strawberry.lazy("api_graphql.types.formula")] | None:
    if self._model.formula:
      from api_graphql.types.formula import FormulaType
      return FormulaType.from_model(self._model.formula)
    
    return None
  
  @strawberry.field
  def production_orders(self) -> list[Annotated["ProductionOrderType", strawberry.lazy("api_graphql.types.production_order")]]:
    from api_graphql.types.production_order import ProductionOrderType
    return [ProductionOrderType.from_model(o) for o in self._model.production_orders]
  
@strawberry.input
class MixSessionIdentifierInput:
  id: Optional[relay.GlobalID] = strawberry.UNSET
  session_number: Optional[str] = strawberry.UNSET
  
  def __post_init__(self):
    if any(v is None for v in vars(self).values()):
      raise GraphQLError(
        "Identifier fields cannot be null.",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )
    
    provided = sum(1 for value in vars(self).values() if value is not strawberry.UNSET)
    if provided != 1:
      raise GraphQLError(
        "Exactly one identifier must be provided.",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )
    
    if self.id is not strawberry.UNSET:
      type_name = self.id.type_name
      expected_name = MixSessionType.__strawberry_definition__.name
      if type_name != expected_name:
        raise GraphQLError(
          f"Expected {expected_name} ID, got {type_name} ID",
          extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
        )

  @property
  def provided(self):
    return next((a, v) for a, v in vars(self).items() if v is not strawberry.UNSET)

  @property
  def query_condition(self):
    attr, value = self.provided
    
    if attr == "id":
      return MixSession.id == value.node_id
    else:
      return getattr(MixSession, attr) == value  

@strawberry.type
class MixSessionCreatePayload:
  mix_session: MixSessionType | None
  feedback: Feedback
  
@strawberry.type
class MixSessionUpdatePayload:
  mix_session: MixSessionType | None
  feedback: Feedback
  
@strawberry.type
class MixSessionDeletePayload:
  feedback: Feedback

@strawberry.type
class MixSessionMergePayload:
  mix_session: MixSessionType | None
  feedback: Feedback