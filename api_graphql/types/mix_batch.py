from __future__ import annotations

from datetime import datetime
from typing import Annotated, TYPE_CHECKING, Optional

from graphql import GraphQLError
from strawberry.scalars import JSON
import strawberry
from strawberry import relay

from api_graphql.types.enums import MixBatchStatusEnum

from api_graphql.types.feedback import Feedback
from models import MixBatch

if TYPE_CHECKING:
  from api_graphql.types.nic_profile import NicProfileType
  from api_graphql.types.production_order import ProductionOrderType

@strawberry.type
class MixBatchType(relay.Node):
  id: relay.NodeID[str]
  mix_number: str
  status: MixBatchStatusEnum
  batch_code: str | None
  recipe_snapshot: JSON | None
  total_volume_ml: float | None
  total_weight_g: float | None
  mixed_at: datetime | None
  nic_profile_full_name_snapshot: str | None
  created_at: datetime
  updated_at: datetime
  
  _model: strawberry.Private[MixBatch]
  
  @classmethod
  def from_model(cls, b: MixBatch) -> "MixBatchType":
    return cls(
      id=b.id,
      mix_number=b.mix_number,
      status=MixBatchStatusEnum[b.status.name],
      batch_code=b.batch_code,
      recipe_snapshot=b.recipe_snapshot,
      total_volume_ml=b.total_volume_ml,
      total_weight_g=b.total_weight_g,
      mixed_at=b.mixed_at,
      nic_profile_full_name_snapshot=b.nic_profile_full_name_snapshot,
      created_at=b.created_at,
      updated_at=b.updated_at,
      _model=b,
    )
    
  @strawberry.field
  def nic_profile(self) -> Annotated["NicProfileType", strawberry.lazy("api_graphql.types.nic_profile")] | None:
    if self._model.nic_profile:
      from api_graphql.types.nic_profile import NicProfileType
      return NicProfileType.from_model(self._model.nic_profile)
    
    return None
  
  @strawberry.field
  def production_orders(self) -> list[Annotated["ProductionOrderType", strawberry.lazy("api_graphql.types.production_order")]]:
    from api_graphql.types.production_order import ProductionOrderType
    return [ProductionOrderType.from_model(o) for o in self._model.production_orders]
  
@strawberry.input
class MixBatchIdentifierInput:
  id: Optional[relay.GlobalID] = strawberry.UNSET
  mix_number: Optional[str] = strawberry.UNSET
  
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
      expected_name = ProductionOrderType.__strawberry_definition__.name
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
      return MixBatch.id == value.node_id
    else:
      return getattr(MixBatch, attr) == value  

@strawberry.type
class MixBatchCreatePayload:
  mix_batch: MixBatchType | None
  feedback: Feedback