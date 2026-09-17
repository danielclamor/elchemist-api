from __future__ import annotations

from datetime import datetime
from typing import Annotated, TYPE_CHECKING, Optional

from graphql import GraphQLError
import strawberry
from strawberry import relay
from strawberry.scalars import JSON

from models import (
  ProductionOrder, 
  ProductionOrderActivityLog, 
  ProductionOrderMixJob, 
  ProductionOrderMixJobStatus, 
  ProductionOrderRepatJob, 
  ProductionOrderRepatJobStatus
)

from api_graphql.types.feedback import Feedback
from api_graphql.types.enums import (
  ProductionOrderActivityEnum,
  ProductionOrderJobEnum, 
  ProductionOrderStatusEnum
)

if TYPE_CHECKING:
  from api_graphql.types.eliquid import EliquidType

@strawberry.type
class ProductionOrderActivityLogType(relay.Node):
  id: relay.NodeID[str]
  activity: ProductionOrderActivityEnum
  old_value: Optional[str] = None
  new_value: Optional[str] = None
  triggered_at: datetime

  @classmethod
  def from_model(cls, l: ProductionOrderActivityLog) -> "ProductionOrderActivityLogType":
    return cls(
      id=l.id,
      activity=ProductionOrderActivityEnum[l.activity.name],
      old_value=l.old_value,
      new_value=l.new_value,
      triggered_at=l.triggered_at,
    )

@strawberry.type
class ProductionOrderMixJobType(relay.Node):
  id: relay.NodeID[str]
  ordered_quantity: int
  produced_quantity: int | None
  batch_number: str | None
  recipe_snapshot: JSON | None
  total_volume_ml: float | None
  total_weight_g: float | None
  status: ProductionOrderMixJobStatus
  is_priority: bool
  created_at: datetime
  
  _model: strawberry.Private[ProductionOrderMixJob]
  
  @classmethod
  def from_model(cls, j: ProductionOrderMixJob) -> "ProductionOrderMixJobType":
    return cls(
      id=j.id,
      ordered_quantity=j.ordered_quantity,
      produced_quantity=j.produced_quantity,
      batch_number=j.batch_number,
      recipe_snapshot=j.recipe_snapshot,
      total_volume_ml=j.total_volume_ml,
      total_weight_g=j.total_weight_g,
      status=j.status,
      is_priority=j.is_priority,
      created_at=j.created_at,
      _model=j,
    )
  
  @strawberry.field
  def production_order(self) -> ProductionOrderType:
    return ProductionOrderType.from_model(self._model.production_order)

@strawberry.input
class ProductionOrderMixJobIdentifierInput:
  id: Optional[relay.GlobalID] = strawberry.UNSET
  production_order_id: Optional[relay.GlobalID] = strawberry.UNSET
  production_order_number: Optional[str] = strawberry.UNSET
  
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
      expected_name = ProductionOrderMixJobType.__strawberry_definition__.name
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
      return ProductionOrderMixJob.id == value.node_id
    elif attr == "production_order_id":
      return ProductionOrderMixJob.production_order_id == value.node_id
    else:
      return getattr(ProductionOrderMixJob, attr) == value

@strawberry.type
class ProductionOrderRepatJobType(relay.Node):
  id: relay.NodeID[str]
  ordered_quantity: int
  incoming_quantity: int | None
  status: ProductionOrderRepatJobStatus
  created_at: datetime
  
  _model: strawberry.Private[ProductionOrderRepatJob]
  
  @classmethod
  def from_model(cls, j: ProductionOrderRepatJob) -> "ProductionOrderRepatJobType":
    return cls(
      id=j.id,
      ordered_quantity=j.ordered_quantity,
      incoming_quantity=j.incoming_quantity,
      status=j.status,
      created_at=j.created_at,
      _model=j,
    )
  
  @strawberry.field
  def production_order(self) -> ProductionOrderType:
    return ProductionOrderType.from_model(self._model.production_order)
  
@strawberry.input
class ProductionOrderRepatJobIdentifierInput:
  id: Optional[relay.GlobalID] = strawberry.UNSET
  production_order_id: Optional[relay.GlobalID] = strawberry.UNSET
  production_order_number: Optional[str] = strawberry.UNSET
  
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
      expected_name = ProductionOrderRepatJobType.__strawberry_definition__.name
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
      return ProductionOrderRepatJob.id == value.node_id
    elif attr == "production_order_id":
      return ProductionOrderRepatJob.production_order_id == value.node_id
    else:
      return getattr(ProductionOrderRepatJob, attr) == value


@strawberry.type
class ProductionOrderType(relay.Node):
  id: relay.NodeID[str]
  order_number: str
  quantity: int | None
  status: ProductionOrderStatusEnum
  job: ProductionOrderJobEnum | None
  is_priority: bool
  created_at: datetime

  _model: strawberry.Private[ProductionOrder]

  @classmethod
  def from_model(cls, o: ProductionOrder) -> "ProductionOrderType":
    return cls(
      id=o.id,
      order_number=o.order_number,
      quantity=o.quantity,
      status=ProductionOrderStatusEnum[o.status.name],
      job=ProductionOrderJobEnum[o.job.name] if o.job else None,
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
  
@strawberry.input
class ProductionOrderCreateInput:
  quantity: int
  is_priority: bool = False

@strawberry.type
class ProductionOrderCreatePayload:
  production_order: ProductionOrderType | None
  feedback: Feedback
  
@strawberry.type
class ProductionOrderJobCreatePayload:
  production_order_job: ProductionOrderMixJobType | ProductionOrderRepatJobType | None
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
class ProductionOrderMixJobUpdatePayload:
  production_order_mix_job: ProductionOrderMixJobType | None
  feedback: Feedback

@strawberry.type
class ProductionOrderRepatJobUpdatePayload:
  production_order_repat_job: ProductionOrderRepatJobType | None
  feedback: Feedback
  
@strawberry.type
class ProductionOrderAssignJobPayload:
  production_order: ProductionOrderType | None
  created_production_order_job: ProductionOrderMixJobType | ProductionOrderRepatJobType | None
  feedback: Feedback