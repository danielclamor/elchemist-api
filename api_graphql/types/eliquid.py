from __future__ import annotations

from typing import Annotated, TYPE_CHECKING

import strawberry
from strawberry import relay

from api_graphql.types.feedback import Feedback
import models
from api_graphql.types.enums import ChillType, NicType, SizeOption, NicLevelOption, BottleColor

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
  
  _model: strawberry.Private["models.Eliquid"]
  
  @classmethod
  def from_model(cls, e: "models.Eliquid") -> "EliquidType":
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
class EliquidIdentifier:
  upc: str

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
  nic_profile_slug: str | None 
  
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
  upc: str | None = strawberry.UNSET
  description: str | None = strawberry.UNSET
  brand: str | None = strawberry.UNSET
  chill_type: ChillType | None = strawberry.UNSET
  nic_type: NicType | None = strawberry.UNSET
  size: SizeOption | None = strawberry.UNSET
  nic_level: NicLevelOption | None = strawberry.UNSET
  bottle_color: BottleColor | None = strawberry.UNSET
  
@strawberry.type
class EliquidUpdatePayload:
  eliquid: EliquidType | None
  feedback: Feedback