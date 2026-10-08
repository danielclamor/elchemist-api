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
  from api_graphql.types.location import LocationType
  from api_graphql.types.production_order import ProductionOrderType

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
  updated_at: datetime
  
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
      updated_at=j.updated_at,
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
  updated_at: datetime
  
  _model: strawberry.Private[ProductionOrderRepatJob]
  
  @classmethod
  def from_model(cls, j: ProductionOrderRepatJob) -> "ProductionOrderRepatJobType":
    return cls(
      id=j.id,
      ordered_quantity=j.ordered_quantity,
      incoming_quantity=j.incoming_quantity,
      status=j.status,
      created_at=j.created_at,
      updated_at=j.updated_at,
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
  
  @strawberry.field
  def production_order(self) -> Annotated["ProductionOrderType", strawberry.lazy("api_graphql.types.production_order")]:
    from api_graphql.types.production_order import ProductionOrderType
    return ProductionOrderType.from_model(self._model.production_order)

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
  location_code: str
  location_name: str

@strawberry.type
class ProductionOrderType(relay.Node):
  id: relay.NodeID[str]
  order_number: str
  ordered_quantity: int | None
  fulfilled_quantity: int | None
  status: ProductionOrderStatusEnum
  job: ProductionOrderJobEnum | None
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
      job=ProductionOrderJobEnum[o.job.name] if o.job else None,
      is_priority=o.is_priority,
      created_at=o.created_at,
      updated_at=o.updated_at,
      _model=o,
    )

  @strawberry.field
  def eliquid(self) -> Annotated["EliquidType", strawberry.lazy("api_graphql.types.eliquid")]:
    from api_graphql.types.eliquid import EliquidType
    return EliquidType.from_model(self._model.eliquid)

  @relay.connection(relay.ListConnection["ProductionOrderActivityLogType"])
  def activity_logs(self) -> list["ProductionOrderActivityLogType"]:
    return [ProductionOrderActivityLogType.from_model(l) for l in self._model.activity_logs]
  
  @relay.connection(relay.ListConnection["ProductionOrderMixJobType"])
  def production_order_mix_jobs(self) -> list["ProductionOrderMixJobType"]:
    return [ProductionOrderMixJobType.from_model(j) for j in self._model.mix_jobs]
  
  @relay.connection(relay.ListConnection["ProductionOrderRepatJobType"])
  def production_order_repat_jobs(self) -> list["ProductionOrderRepatJobType"]:
    return [ProductionOrderRepatJobType.from_model(j) for j in self._model.repat_jobs]
  
  @strawberry.field
  def allocation_hq(self, info: strawberry.Info) -> ProductionOrderHqAllocationType | None:
    from api_graphql.resolvers.location import get_hq_location

    hq = get_hq_location(info.context["db"])

    if hq is None:
      return None

    return ProductionOrderHqAllocationType(
      quantity=self._model.hq_quantity,
      location_code=hq.code,
      location_name=hq.name,
    )
  
  @relay.connection(relay.ListConnection["ProductionOrderAllocationType"])
  def allocations(self) -> list["ProductionOrderAllocationType"]:
    return [ProductionOrderAllocationType.from_model(a) for a in self._model.allocations]

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

@strawberry.input
class ProductionOrderMixJobFlavoringParametersInput:
  name: str
  is_vg: bool
  ratio: float
  
@strawberry.input
class ProductionOrderMixJobNicBaseParametersInput:
  code: str
  name: str
  is_vg: bool
  ratio: float

@strawberry.input
class ProductionOrderMixJobParametersInput:
  batch_volume_ml: float
  target_nic_str: float
  target_pg: float
  target_vg: float
  nic_base_nic_str: float
  flavorings: list[ProductionOrderMixJobFlavoringParametersInput]
  nic_bases: list[ProductionOrderMixJobNicBaseParametersInput]

@strawberry.input
class ProductionOrderMixJobIngredientInput:
  name: str
  ratio: float
  volume_ml: float
  weight_g: float

@strawberry.input
class ProductionOrderMixJobRecipeInput:
  mix_parameters: ProductionOrderMixJobParametersInput
  ingredients: list[ProductionOrderMixJobIngredientInput]
  total_ratio: float
  total_volume_ml: float
  total_weight_g: float
  nic_profile_slug: str

@strawberry.input
class ProductionOrderMixJobMarkMixedInput:
  recipe: ProductionOrderMixJobRecipeInput
  produced_quantity: int

@strawberry.type
class ProductionOrderMixJobUpdatePayload:
  production_order_mix_job: ProductionOrderMixJobType | None
  feedback: Feedback

@strawberry.input
class ProductionOrderRepatJobMarkCompletedInput:
  incoming_quantity: int

@strawberry.type
class ProductionOrderRepatJobUpdatePayload:
  production_order_repat_job: ProductionOrderRepatJobType | None
  feedback: Feedback
  
@strawberry.type
class ProductionOrderAssignJobPayload:
  production_order: ProductionOrderType | None
  created_production_order_job: ProductionOrderMixJobType | ProductionOrderRepatJobType | None
  feedback: Feedback