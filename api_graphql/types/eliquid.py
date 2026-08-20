from __future__ import annotations

import strawberry
from strawberry import relay

import models
from api_graphql.types.enums import ChillType, NicType, SizeOption, NicLevelOption, BottleColor

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from api_graphql.types.nic_profile import NicProfileType
  from api_graphql.types.production_order import ProductionOrderType

@strawberry.type
class EliquidType(relay.Node):
  upc: relay.NodeID[str]
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
  def nic_profile(self) -> "NicProfileType":
    from api_graphql.types.nic_profile import NicProfileType
    return NicProfileType.from_model(self._model.nic_profile)
  
  @strawberry.field
  def production_orders(self) -> list["ProductionOrderType"]:
    from api_graphql.types.production_order import ProductionOrderType
    return [ProductionOrderType.from_model(o) for o in self._model.production_orders]