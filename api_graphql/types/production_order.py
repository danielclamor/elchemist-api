from __future__ import annotations

from datetime import datetime
from typing import Annotated, TYPE_CHECKING, Optional

from graphql import GraphQLError
import strawberry
from strawberry import relay
from strawberry.scalars import JSON

from api_graphql.types.location import LocationIdentifierInput
from models import (
  ProductionOrder, 
  ProductionOrderActivityLog,
  ProductionOrderAllocation, 
)

from api_graphql.types.feedback import Feedback
from api_graphql.types.enums import (
  ProductionOrderActivityTypeEnum,
  ProductionOrderJobTypeEnum,
  ProductionOrderStatusEnum,
)

if TYPE_CHECKING:
  from api_graphql.types.eliquid import EliquidType
  from api_graphql.types.location import LocationType
  from api_graphql.types.production_order import ProductionOrderType
  from api_graphql.types.mix_session import MixSessionType

@strawberry.type
class ProductionOrderActivityLogType(relay.Node):
  id: relay.NodeID[str]
  type: ProductionOrderActivityTypeEnum
  old_value: Optional[str] = None
  new_value: Optional[str] = None
  triggered_at: datetime

  @classmethod
  def from_model(cls, l: ProductionOrderActivityLog) -> "ProductionOrderActivityLogType":
    return cls(
      id=l.id,
      type=ProductionOrderActivityTypeEnum[l.type.name],
      old_value=l.old_value,
      new_value=l.new_value,
      triggered_at=l.triggered_at,
    )

@strawberry.type
class ProductionOrderAllocationType(relay.Node):
  id: relay.NodeID[str]
  quantity: int
  
  _model: strawberry.Private[ProductionOrderAllocation]
  
  @classmethod
  def from_model(cls, a: ProductionOrderAllocation) -> "ProductionOrderAllocationType":
    return cls(
      id=a.id,
      quantity=a.quantity,
      _model=a,
    )
    
  @strawberry.field
  def location(self) -> Annotated["LocationType", strawberry.lazy("api_graphql.types.location")]:
    from api_graphql.types.location import LocationType
    return LocationType.from_model(self._model.location)

@strawberry.input
class ProductionOrderAllocationInput:
  location_identifier: LocationIdentifierInput
  quantity: int

  def __post_init__(self):
    if self.quantity <= 0:
      raise GraphQLError(
        "Allocation quantity must be greater than 0.",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )
      
@strawberry.type
class ProductionOrderHqAllocationType:
  quantity: int | None
  is_projected: bool
  location_code: str
  location_name: str

@strawberry.type
class ProductionOrderType(relay.Node):
  id: relay.NodeID[str]
  order_number: str
  ordered_quantity: int | None
  fulfilled_quantity: int | None
  status: ProductionOrderStatusEnum
  job_type: ProductionOrderJobTypeEnum | None
  is_priority: bool
  created_at: datetime
  updated_at: datetime

  _model: strawberry.Private[ProductionOrder]

  @classmethod
  def from_model(cls, o: ProductionOrder) -> "ProductionOrderType":
    return cls(
      id=o.id,
      order_number=o.order_number,
      ordered_quantity=o.ordered_quantity,
      fulfilled_quantity=o.fulfilled_quantity,
      status=ProductionOrderStatusEnum[o.status.name],
      job_type=ProductionOrderJobTypeEnum[o.job_type.name] if o.job_type else None,
      is_priority=o.is_priority,
      created_at=o.created_at,
      updated_at=o.updated_at,
      _model=o,
    )

  @strawberry.field
  def is_open(self) -> bool:
    return self._model.is_open

  @strawberry.field
  def eliquid(self) -> Annotated["EliquidType", strawberry.lazy("api_graphql.types.eliquid")]:
    from api_graphql.types.eliquid import EliquidType
    return EliquidType.from_model(self._model.eliquid)

  @strawberry.field
  def activity_logs(self) -> list[ProductionOrderActivityLogType]:
    return [ProductionOrderActivityLogType.from_model(l) for l in self._model.activity_logs]
  
  @strawberry.field
  def mix_session(self) -> Annotated["MixSessionType", strawberry.lazy("api_graphql.types.mix_session")] | None:
    from api_graphql.types.mix_session import MixSessionType
    return MixSessionType.from_model(self._model.mix_session) if self._model.mix_session else None
  
  @strawberry.field
  def allocation_hq(self) -> ProductionOrderHqAllocationType | None:
    hq = self._model.hq_location

    if hq is None:
      return None

    return ProductionOrderHqAllocationType(
      quantity=self._model.hq_quantity,
      is_projected=self._model.is_hq_quantity_projected,
      location_code=hq.code,
      location_name=hq.name,
    )
  
  @strawberry.field
  def allocations(self) -> list[ProductionOrderAllocationType]:
    return [ProductionOrderAllocationType.from_model(a) for a in self._model.allocations]

  @strawberry.field
  def allocated_quantity(self) -> int:
    return self._model.allocated_quantity

  @strawberry.field
  def allocation_shortfall(self) -> int | None:
    return self._model.allocation_shortfall

@strawberry.input
class ProductionOrderIdentifierInput:
  id: Optional[relay.GlobalID] = strawberry.UNSET
  order_number: Optional[str] = strawberry.UNSET
  
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
      return ProductionOrder.id == value.node_id
    else:
      return getattr(ProductionOrder, attr) == value

@strawberry.type
class ProductionOrderStatusCountType:
  status: ProductionOrderStatusEnum
  count: int

@strawberry.input
class ProductionOrderCreateInput:
  quantity: Optional[int] = strawberry.UNSET
  is_priority: bool = False
  allocations: Optional[list[ProductionOrderAllocationInput]] = strawberry.UNSET
  job_type: Optional[ProductionOrderJobTypeEnum] = strawberry.UNSET

@strawberry.type
class ProductionOrderCreatePayload:
  production_order: ProductionOrderType | None
  feedback: Feedback
  
@strawberry.type
class ProductionOrderDeletePayload:
  deleted_order_number: str | None
  feedback: Feedback
  
@strawberry.input
class ProductionOrderUpdateInput:
  status: Optional[ProductionOrderStatusEnum] = strawberry.UNSET
  quantity: Optional[int] = strawberry.UNSET
  is_priority: Optional[bool] = strawberry.UNSET
  
@strawberry.type
class ProductionOrderUpdatePayload:
  production_order: ProductionOrderType | None
  feedback: Feedback
  
@strawberry.type
class ProductionOrderAssignMixSessionPayload:
  production_order: ProductionOrderType | None
  feedback: Feedback

@strawberry.type
class ProductionOrderBulkAssignMixSessionPayload:
  production_order_assign_payloads: list[ProductionOrderAssignMixSessionPayload]
  feedback: Feedback