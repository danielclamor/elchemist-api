from __future__ import annotations

from typing import Annotated, TYPE_CHECKING, Optional

from graphql import GraphQLError
import strawberry
from strawberry import relay

from models import Eliquid

from api_graphql.types.feedback import Feedback
from api_graphql.types.nic_profile import NicProfileIdentifierInput

from api_graphql.types.enums import (
  ChillType, 
  NicType, 
  SizeOption, 
  NicLevelOption, 
  BottleColor
)

if TYPE_CHECKING:
  from api_graphql.types.nic_profile import NicProfileType
  from api_graphql.types.production_order import ProductionOrderType

@strawberry.type
class EliquidType(relay.Node):
  id: relay.NodeID[str]
  upc: str
  description: str
  brand: str
  chill_type: ChillType
  nic_type: NicType
  size: SizeOption
  nic_level: NicLevelOption
  bottle_color: BottleColor
  
  _model: strawberry.Private["Eliquid"]
  
  @classmethod
  def from_model(cls, e: "Eliquid") -> "EliquidType":
    return cls(
      id=e.id,
      upc=e.upc,
      description=e.description,
      brand=e.brand,
      chill_type=ChillType[e.chill_type.name],
      nic_type=NicType[e.nic_type.name],
      size=SizeOption[e.size.name],
      nic_level=NicLevelOption[e.nic_level.name],
      bottle_color=BottleColor[e.bottle_color.name],
      _model=e,
    )
    
  @strawberry.field
  def nic_profile(self) -> Annotated["NicProfileType", strawberry.lazy("api_graphql.types.nic_profile")] | None:
    if self._model.nic_profile:
      from api_graphql.types.nic_profile import NicProfileType
      return NicProfileType.from_model(self._model.nic_profile)

    return None
  
  @relay.connection(relay.ListConnection[Annotated["ProductionOrderType", strawberry.lazy("api_graphql.types.production_order")]])
  def production_orders(self) -> list[Annotated["ProductionOrderType", strawberry.lazy("api_graphql.types.production_order")]]:
    from api_graphql.types.production_order import ProductionOrderType
    return [ProductionOrderType.from_model(o) for o in self._model.production_orders]

@strawberry.input
class EliquidIdentifierInput:
  id: Optional[relay.GlobalID] = strawberry.UNSET
  upc: Optional[str] = strawberry.UNSET
  
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
      expected_name = EliquidType.__strawberry_definition__.name
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
      return Eliquid.id == value.node_id
    else:
      return getattr(Eliquid, attr) == value

@strawberry.input
class EliquidCreateInput:
  upc: str
  description: str
  brand: str
  chill_type: ChillType
  nic_type: NicType
  size: SizeOption
  nic_level: NicLevelOption
  bottle_color: BottleColor
  nic_profile: Optional[NicProfileIdentifierInput] = strawberry.UNSET
  
@strawberry.type
class EliquidCreatePayload:
  eliquid: EliquidType | None
  feedback: Feedback
  
@strawberry.type
class EliquidDeletePayload:
  deleted_upc: str | None
  deleted_description: str | None
  feedback: Feedback

@strawberry.input
class EliquidUpdateInput:
  upc: Optional[str] = strawberry.UNSET
  description: Optional[str] = strawberry.UNSET
  brand: Optional[str] = strawberry.UNSET
  chill_type: Optional[ChillType] = strawberry.UNSET
  nic_type: Optional[NicType] = strawberry.UNSET
  size: Optional[SizeOption] = strawberry.UNSET
  nic_level: Optional[NicLevelOption] = strawberry.UNSET
  bottle_color: Optional[BottleColor] = strawberry.UNSET
  
@strawberry.type
class EliquidUpdatePayload:
  eliquid: EliquidType | None
  feedback: Feedback