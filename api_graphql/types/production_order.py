from __future__ import annotations

from datetime import datetime
from typing import Annotated, TYPE_CHECKING

import strawberry
from strawberry import relay

import models
from api_graphql.types.feedback import Feedback
from api_graphql.types.enums import ProductionOrderActivity, ProductionOrderStatus

if TYPE_CHECKING:
  from api_graphql.types.eliquid import EliquidType

@strawberry.type
class ProductionOrderActivityLogType(relay.Node):
  id: relay.NodeID[str]
  activity: ProductionOrderActivity
  old_value: str | None
  new_value: str | None
  triggered_at: datetime

  @classmethod
  def from_model(cls, l: models.ProductionOrderActivityLog) -> "ProductionOrderActivityLogType":
    return cls(
      id=l.id,
      activity=ProductionOrderActivity[l.activity.name],
      old_value=l.old_value,
      new_value=l.new_value,
      triggered_at=l.triggered_at,
    )

@strawberry.type
class ProductionOrderType(relay.Node):
  id: relay.NodeID[str]
  order_number: str
  quantity: int
  status: ProductionOrderStatus
  is_priority: bool
  created_at: datetime

  _model: strawberry.Private[models.ProductionOrder]

  @classmethod
  def from_model(cls, o: models.ProductionOrder) -> "ProductionOrderType":
    return cls(
      id=o.id,
      order_number=o.order_number,
      quantity=o.quantity,
      status=ProductionOrderStatus[o.status.name],
      is_priority=o.is_priority,
      created_at=o.created_at,
      _model=o,
    )

  @strawberry.field
  def eliquid(self) -> Annotated["EliquidType", strawberry.lazy("api_graphql.types.eliquid")]:
    from api_graphql.types.eliquid import EliquidType
    return EliquidType.from_model(self._model.eliquid)

  @relay.connection(relay.ListConnection["ProductionOrderActivityLogType"])
  def activity_logs(self) -> list["ProductionOrderActivityLogType"]:
    return [ProductionOrderActivityLogType.from_model(l) for l in self._model.activity_logs]
  
@strawberry.input
class ProductionOrderCreateInput:
  eliquid_upc: str
  quantity: int
  is_priority: bool | None = None

@strawberry.type
class ProductionOrderCreatePayload:
  production_order: ProductionOrderType | None
  feedback: Feedback