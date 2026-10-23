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
  MixJob, 
  RepatJob,
)

from api_graphql.types.feedback import Feedback
from api_graphql.types.enums import (
  ProductionOrderActivityTypeEnum,
  ProductionOrderJobStatusEnum,
  ProductionOrderJobTypeEnum,
  ProductionOrderStatusEnum,
)

if TYPE_CHECKING:
  from api_graphql.types.eliquid import EliquidType
  from api_graphql.types.location import LocationType
  from api_graphql.types.production_order import ProductionOrderType

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
class MixJobType(relay.Node):
  id: relay.NodeID[str]
  job_number: str
  ordered_quantity: int
  produced_quantity: int | None
  batch_number: str | None
  recipe_snapshot: JSON | None
  total_volume_ml: float | None
  total_weight_g: float | None
  status: ProductionOrderJobStatusEnum
  created_at: datetime
  updated_at: datetime
  
  _model: strawberry.Private[MixJob]
  
  @classmethod
  def from_model(cls, j: MixJob) -> "MixJobType":
    return cls(
      id=j.id,
      job_number=j.job_number,
      ordered_quantity=j.ordered_quantity,
      produced_quantity=j.produced_quantity,
      batch_number=j.batch_number,
      recipe_snapshot=j.recipe_snapshot,
      total_volume_ml=j.total_volume_ml,
      total_weight_g=j.total_weight_g,
      status=ProductionOrderJobStatusEnum[j.status.name],
      created_at=j.created_at,
      updated_at=j.updated_at,
      _model=j,
    )
  
  @strawberry.field
  def production_order(self) -> ProductionOrderType:
    return ProductionOrderType.from_model(self._model.production_order)

@strawberry.input
class MixJobIdentifierInput:
  id: Optional[relay.GlobalID] = strawberry.UNSET
  job_number: Optional[str] = strawberry.UNSET
  
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
      expected_name = MixJobType.__strawberry_definition__.name
      if type_name != expected_name:
        raise GraphQLError(
          f"Expected {expected_name} ID, got {type_name} ID",
          extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
        )
        
    if self.job_number is not strawberry.UNSET:
      self.job_number = self.job_number.strip().upper()    
      
  @property
  def provided(self):
    return next((a, v) for a, v in vars(self).items() if v is not strawberry.UNSET)

  @property
  def query_condition(self):
    attr, value = self.provided
    
    if attr == "id":
      return MixJob.id == value.node_id
    else:
      return getattr(MixJob, attr) == value

@strawberry.type
class RepatJobType(relay.Node):
  id: relay.NodeID[str]
  job_number: str
  ordered_quantity: int | None
  incoming_quantity: int | None
  status: ProductionOrderJobStatusEnum
  created_at: datetime
  updated_at: datetime
  
  _model: strawberry.Private[RepatJob]
  
  @classmethod
  def from_model(cls, j: RepatJob) -> "RepatJobType":
    return cls(
      id=j.id,
      job_number=j.job_number,
      ordered_quantity=j.ordered_quantity,
      incoming_quantity=j.incoming_quantity,
      status=ProductionOrderJobStatusEnum[j.status.name],
      created_at=j.created_at,
      updated_at=j.updated_at,
      _model=j,
    )
  
  @strawberry.field
  def production_order(self) -> ProductionOrderType:
    return ProductionOrderType.from_model(self._model.production_order)
  
@strawberry.input
class RepatJobIdentifierInput:
  id: Optional[relay.GlobalID] = strawberry.UNSET
  job_number: Optional[str] = strawberry.UNSET
  
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
      expected_name = RepatJobType.__strawberry_definition__.name
      if type_name != expected_name:
        raise GraphQLError(
          f"Expected {expected_name} ID, got {type_name} ID",
          extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
        )
        
    if self.job_number is not strawberry.UNSET:
      self.job_number = self.job_number.strip().upper()
  
  @property
  def provided(self):
    return next((a, v) for a, v in vars(self).items() if v is not strawberry.UNSET)

  @property
  def query_condition(self):
    attr, value = self.provided
    
    if attr == "id":
      return RepatJob.id == value.node_id
    else:
      return getattr(RepatJob, attr) == value

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
  def activity_logs(self) -> list["ProductionOrderActivityLogType"]:
    return [ProductionOrderActivityLogType.from_model(l) for l in self._model.activity_logs]
  
  @relay.connection(relay.ListConnection["MixJobType"])
  def mix_jobs(self) -> list["MixJobType"]:
    return [MixJobType.from_model(j) for j in self._model.mix_jobs]
  
  @relay.connection(relay.ListConnection["RepatJobType"])
  def repat_jobs(self) -> list["RepatJobType"]:
    return [RepatJobType.from_model(j) for j in self._model.repat_jobs]
  
  @strawberry.field
  def current_job(self) -> MixJobType | RepatJobType | None:
    job = self._model.current_job

    if isinstance(job, MixJob):
      return MixJobType.from_model(job)
    if isinstance(job, RepatJob):
      return RepatJobType.from_model(job)

    return None
  
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
  def allocations(self) -> list["ProductionOrderAllocationType"]:
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
class ProductionOrderJobCreatePayload:
  production_order_job: MixJobType | RepatJobType | None
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
class MixJobFlavoringParametersInput:
  name: str
  is_vg: bool
  ratio: float
  
@strawberry.input
class MixJobNicBaseParametersInput:
  code: str
  name: str
  is_vg: bool
  ratio: float

@strawberry.input
class MixJobParametersInput:
  batch_volume_ml: float
  target_nic_str: float
  target_pg: float
  target_vg: float
  nic_base_nic_str: float
  flavorings: list[MixJobFlavoringParametersInput]
  nic_bases: list[MixJobNicBaseParametersInput]

@strawberry.input
class MixJobIngredientInput:
  name: str
  ratio: float
  volume_ml: float
  weight_g: float

@strawberry.input
class MixJobRecipeInput:
  mix_parameters: MixJobParametersInput
  ingredients: list[MixJobIngredientInput]
  total_ratio: float
  total_volume_ml: float
  total_weight_g: float
  nic_profile_slug: str

@strawberry.input
class MixJobMarkMixedInput:
  recipe: MixJobRecipeInput
  produced_quantity: int

@strawberry.type
class MixJobUpdatePayload:
  mix_job: MixJobType | None
  feedback: Feedback

@strawberry.input
class RepatJobMarkCompletedInput:
  incoming_quantity: int

@strawberry.type
class RepatJobUpdatePayload:
  repat_job: RepatJobType | None
  feedback: Feedback
  
@strawberry.type
class ProductionOrderAssignJobPayload:
  production_order: ProductionOrderType | None
  created_production_order_job: MixJobType | RepatJobType | None
  feedback: Feedback