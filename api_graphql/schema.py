from datetime import datetime

from graphql import GraphQLError
import strawberry
from strawberry import relay
from typing import List, Optional

from api_graphql.types.connections import ListConnectionWithTotalCount
from api_graphql.types.brand import BrandEdge, BrandConnection
from api_graphql.types.eliquid import (
  EliquidType,
  EliquidCreateInput, 
  EliquidCreatePayload,
  EliquidDeletePayload,
  EliquidIdentifierInput,
  EliquidUpdateInput, 
  EliquidUpdatePayload,
)
from api_graphql.types.enums import ProductionOrderJobTypeEnum, ProductionOrderStatusEnum
from api_graphql.types.flavoring_option import (
  FlavoringOptionsBulkDeletePayload,
  FlavoringOptionDeletePayload,
  FlavoringOptionType,
  FlavoringOptionIdentifierInput,
  FlavoringOptionCreateInput,
  FlavoringOptionCreatePayload,
  FlavoringOptionsBulkCreatePayload,
)
from api_graphql.types.mix_session import MixSessionCreatePayload, MixSessionIdentifierInput, MixSessionType, MixSessionUpdatePayload
from api_graphql.types.nic_base_option import (
  NicBaseOptionType,
  NicBaseOptionIdentifierInput,
  NicBaseOptionCreateInput,
  NicBaseOptionCreatePayload,
  NicBaseOptionsBulkCreatePayload,
  NicBaseOptionDeletePayload,
  NicBaseOptionsBulkDeletePayload,
)
from api_graphql.types.formula import (
  FormulaNicBasesSetPayload,
  FormulaType,
  FormulaIdentifierInput,
  FormulaCreateInput,
  FormulaCreatePayload,
  FormulaDeletePayload,
  FormulaUpdateInput,
  FormulaUpdatePayload,
  FormulaFlavoringInput,
  FormulaFlavoringIdentifierInput,
  FormulaFlavoringsBulkAddPayload,
  FormulaFlavoringsBulkRemovePayload,
  FormulaNicBaseInput,
  FormulaNicBaseIdentifierInput,
  FormulaNicBasesBulkAddPayload,
  FormulaNicBasesBulkRemovePayload,
)

from api_graphql.types.recipe import (
  RecipeType,
  RecipeInput,
  RecipeDiyType,
  RecipeDiyInput,
)

from api_graphql.types.production_order import (
  ProductionOrderStatusCountType,
  ProductionOrderType,
  ProductionOrderIdentifierInput,
  ProductionOrderCreateInput,
  ProductionOrderCreatePayload,
  ProductionOrderDeletePayload,
  ProductionOrderUpdateInput,
  ProductionOrderUpdatePayload,
)

from api_graphql.types.location import (
  LocationType,
  LocationIdentifierInput,
  LocationUpdatePayload,
)

from api_graphql.resolvers.brand import (
  get_all_brands,
)

from api_graphql.resolvers.eliquid import (
  create_eliquid,
  delete_eliquid,
  get_all_eliquids,
  get_eliquid,
  set_eliquid_formula,
  unset_eliquid_formula,
  update_eliquid,
)

from api_graphql.resolvers.formula import (
  bulk_add_formula_flavorings,
  bulk_add_formula_nic_bases,
  bulk_remove_formula_flavorings,
  bulk_remove_formula_nic_bases,
  create_formula,
  delete_formula,
  get_all_formulas,
  get_formula,
  set_formula_nic_bases,
  update_formula,
)

from api_graphql.resolvers.flavoring_option import (
  bulk_create_flavoring_options,
  bulk_delete_flavoring_options,
  create_flavoring_option,
  delete_flavoring_option,
  get_all_flavoring_options,
  get_flavoring_option,
)

from api_graphql.resolvers.nic_base_option import (
  bulk_create_nic_base_options,
  create_nic_base_option,
  delete_nic_base_option,
  bulk_delete_nic_base_options,
  get_all_nic_base_options,
  get_nic_base_option,
)

from api_graphql.resolvers.recipe import (
  get_recipe,
  get_recipe_diy,
)

from api_graphql.resolvers.production_order import (
  create_production_order,
  delete_production_order,
  get_all_production_orders,
  get_production_order,
  get_production_order_status_counts,
  mark_production_order_cancelled,
  mark_production_order_delivered,
  mark_production_order_fulfilled,
  mark_production_order_in_progress,
  set_production_order_archived,
  set_production_order_priority,
  set_production_order_ordered_quantity,
  update_production_order,
)

from api_graphql.resolvers.mix_session import (
  create_mix_session, 
  get_all_mix_sessions, 
  get_mix_session, 
  mark_mix_session_completed, 
  mark_mix_session_mixed,
)


from api_graphql.resolvers.location import (
  get_all_locations,
  get_hq_location,
  get_location,
  set_location_archived,
)

from models import ProductionOrderJobType, ProductionOrderStatus

def _cursor_index(cursor: str) -> int:
  return int(relay.from_base64(cursor).split(":")[1])

def _validate_pagination_args(first, last, after, before) -> None:
  if first is not None and last is not None:
    raise GraphQLError(
      "Passing both `first` and `last` is not supported — use `first`/`after` "
      "for forward pagination or `last`/`before` for backward pagination."
    )

  if (after is not None or before is not None) and (first is None and last is None):
    raise GraphQLError(
      "You must provide a `first` or `last`"
    )

def _paginate_brands(
  brands: List[str],
  after: Optional[str],
  before: Optional[str],
  first: Optional[int],
  last: Optional[int],
) -> BrandConnection:
  start, end = 0, len(brands)
  _validate_pagination_args(first, last, after, before)
  if after is not None:
    start = max(start, _cursor_index(after) + 1)
  if before is not None:
    end = min(end, _cursor_index(before))

  if first is not None:
    end = min(end, start + first)
  elif last is not None:
    start = max(start, end - last)

  page = sorted(brands[start:end])

  edges = [
    BrandEdge(cursor=relay.to_base64("brandindex", str(start + i)), node=b)
    for i, b in enumerate(page)
  ]

  return BrandConnection(
    edges=edges,
    page_info=relay.PageInfo(
      has_previous_page=start > 0,
      has_next_page=end < len(brands),
      start_cursor=edges[0].cursor if edges else None,
      end_cursor=edges[-1].cursor if edges else None,
    ),
  )


@strawberry.type
class Query:
  @strawberry.field
  def brands(
    self, info: strawberry.Info, 
    after: Optional[str] = None, 
    before: Optional[str] = None, 
    first: Optional[int] = None, 
    last: Optional[int] = None,
  ) -> BrandConnection:
    db = info.context["db"]
    return _paginate_brands(get_all_brands(db=db), after, before, first, last)

  @strawberry.field
  def eliquid(
    self, info: strawberry.Info, identifier: EliquidIdentifierInput,
  ) -> EliquidType | None:
    db = info.context["db"]
    e = get_eliquid(db=db, identifier=identifier)
    return EliquidType.from_model(e) if e else None
  
  @relay.connection(relay.ListConnection[EliquidType])
  def eliquids(
    self, info: strawberry.Info,
  ) -> List[EliquidType]:
    db = info.context["db"]
    return [EliquidType.from_model(e) for e in get_all_eliquids(db)]
  
  @strawberry.field
  def flavoringOption(
    self, info: strawberry.Info, identifier: FlavoringOptionIdentifierInput,
  ) -> FlavoringOptionType | None:
    db = info.context["db"]
    o = get_flavoring_option(db=db, identifier=identifier)
    return FlavoringOptionType.from_model(o) if o else None

  @relay.connection(relay.ListConnection[FlavoringOptionType])
  def flavoringOptions(
    self, info: strawberry.Info,
  ) -> List[FlavoringOptionType]:
    db = info.context["db"]
    return [FlavoringOptionType.from_model(o) for o in get_all_flavoring_options(db)]
  
  @strawberry.field
  def nicBaseOption(
    self, info: strawberry.Info, identifier: NicBaseOptionIdentifierInput,
  ) -> NicBaseOptionType | None:
    db = info.context["db"]
    o = get_nic_base_option(db=db, identifier=identifier)
    return NicBaseOptionType.from_model(o) if o else None

  @relay.connection(relay.ListConnection[NicBaseOptionType])
  def nicBaseOptions(
    self, info: strawberry.Info,
  ) -> List[NicBaseOptionType]:
    db = info.context["db"]
    return [NicBaseOptionType.from_model(o) for o in get_all_nic_base_options(db)]

  @strawberry.field
  def formula(
    self, info: strawberry.Info, identifier: FormulaIdentifierInput,
  ) -> FormulaType | None:
    db = info.context["db"]
    p = get_formula(db=db, identifier=identifier)
    return FormulaType.from_model(p) if p else None
  
  @relay.connection(relay.ListConnection[FormulaType])
  def formulas(
    self, info: strawberry.Info,
  ) -> List[FormulaType]:
    db = info.context["db"]
    return [FormulaType.from_model(p) for p in get_all_formulas(db)]
  
  @strawberry.field
  def recipe(
    self, info: strawberry.Info, formula_identifier: FormulaIdentifierInput, input: RecipeInput,
  ) -> RecipeType | None:
    db = info.context["db"]
    return get_recipe(db=db, formula_identifier=formula_identifier, input=input)
  
  @strawberry.field
  def recipeDiy(
    self, input: RecipeDiyInput,
  ) -> RecipeDiyType:
    return get_recipe_diy(input=input)
  
  @strawberry.field
  def productionOrder(
    self, info: strawberry.Info, identifier: ProductionOrderIdentifierInput,
  ) -> ProductionOrderType | None:
    db = info.context["db"]
    o = get_production_order(db, identifier=identifier)
    return ProductionOrderType.from_model(o) if o else None
  
  @relay.connection(ListConnectionWithTotalCount[ProductionOrderType])
  def productionOrders(
    self, info: strawberry.Info,
    job_type: Optional[ProductionOrderJobTypeEnum] = None,
    status: Optional[ProductionOrderStatusEnum] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
  ) -> List[ProductionOrderType]:
    db = info.context["db"]
    model_job_type = ProductionOrderJobType[job_type.name] if job_type else None
    model_status = ProductionOrderStatus[status.name] if status else None
    return [ProductionOrderType.from_model(po) for po in
            get_all_production_orders(db, model_job_type, model_status, created_from, created_to)]

  @strawberry.field
  def productionOrderStatusCounts(
    self, info: strawberry.Info,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
  ) -> List[ProductionOrderStatusCountType]:
    db = info.context["db"]
    counts = get_production_order_status_counts(db, created_from, created_to)
    return [ProductionOrderStatusCountType(status=ProductionOrderStatusEnum[s.name], count=counts.get(s, 0))
            for s in ProductionOrderStatus]
  
  @strawberry.field
  def mixSession(
    self, info: strawberry.Info, identifier: MixSessionIdentifierInput,
  ) -> MixSessionType | None:
    db = info.context["db"]
    b = get_mix_session(db, identifier=identifier)
    return MixSessionType.from_model(b) if b else None
  
  @relay.connection(ListConnectionWithTotalCount[MixSessionType])
  def mixSessions(
    self, info: strawberry.Info,
  ) -> List[MixSessionType]:
    db = info.context["db"]
    return [MixSessionType.from_model(b) for b in get_all_mix_sessions(db)]
  
  @strawberry.field
  def location(
    self, info: strawberry.Info, identifier: LocationIdentifierInput,
  ) -> LocationType | None:
    db = info.context["db"]
    l = get_location(db, identifier=identifier)
    return LocationType.from_model(l) if l else None
  
  @strawberry.field
  def locationHq(
    self, info: strawberry.Info,
  ) -> LocationType | None:
    db = info.context["db"]
    l = get_hq_location(db)
    return LocationType.from_model(l) if l else None
  
  @relay.connection(relay.ListConnection[LocationType])
  def locations(
    self, info: strawberry.Info, include_archived: bool = False,
  ) -> List[LocationType]:
    db = info.context["db"]
    return [LocationType.from_model(l) for l in get_all_locations(db, include_archived=include_archived)]

@strawberry.type
class Mutation:
  @strawberry.mutation
  def eliquidCreate(
    self, info: strawberry.Info, eliquid: EliquidCreateInput,
  ) -> EliquidCreatePayload:
    db = info.context["db"]
    return create_eliquid(
      db=db, input=eliquid,
    )
  
  @strawberry.mutation
  def eliquidDelete(
    self, info: strawberry.Info, identifier: EliquidIdentifierInput,
  ) -> EliquidDeletePayload:
    db = info.context["db"]
    return delete_eliquid(
      db=db, identifier=identifier,
    )
  
  @strawberry.mutation
  def eliquidFormulaSet(
    self, info: strawberry.Info, identifier: EliquidIdentifierInput, formula_identifier: FormulaIdentifierInput,
  ) -> EliquidUpdatePayload:
    db = info.context["db"]
    return set_eliquid_formula(
      db=db, identifier=identifier, formula_identifier=formula_identifier,
    )
  
  @strawberry.mutation
  def eliquidFormulaUnset(
    self, info: strawberry.Info, identifier: EliquidIdentifierInput,
  ) -> EliquidUpdatePayload:
    db = info.context["db"]
    return unset_eliquid_formula(
      db=db, identifier=identifier,
    )
  
  @strawberry.mutation
  def eliquidUpdate(
    self, info: strawberry.Info, identifier: EliquidIdentifierInput, eliquid: EliquidUpdateInput,
  ) -> EliquidUpdatePayload:
    db = info.context["db"]
    return update_eliquid(
      db=db, identifier=identifier, input=eliquid,
    )
  
  @strawberry.mutation
  def flavoringOptionCreate(
    self, info: strawberry.Info, flavoring_option: FlavoringOptionCreateInput,
  ) -> FlavoringOptionCreatePayload:
    db = info.context["db"]
    return create_flavoring_option(
      db=db, input=flavoring_option,
    )
  
  @strawberry.mutation
  def flavoringOptionsBulkCreate(
    self, info: strawberry.Info, flavoring_options: list[FlavoringOptionCreateInput],
  ) -> FlavoringOptionsBulkCreatePayload:
    db = info.context["db"]
    return bulk_create_flavoring_options(
      db=db, inputs=flavoring_options,
    )
  
  @strawberry.mutation
  def flavoringOptionDelete(
    self, info: strawberry.Info, identifier: FlavoringOptionIdentifierInput,
  ) -> FlavoringOptionDeletePayload:
    db = info.context["db"]
    return delete_flavoring_option(
      db=db, identifier=identifier,
    )
  
  @strawberry.mutation
  def flavoringOptionsBulkDelete(
    self, info: strawberry.Info, identifiers: list[FlavoringOptionIdentifierInput],
  ) -> FlavoringOptionsBulkDeletePayload:
    db = info.context["db"]
    return bulk_delete_flavoring_options(
      db=db, identifiers=identifiers,
    )
    
  @strawberry.mutation
  def mixSessionCreate(
    self, info: strawberry.Info, formula_identifier: FormulaIdentifierInput,
  ) -> MixSessionCreatePayload:
    db = info.context["db"]
    return create_mix_session(
      db=db, formula_identifier=formula_identifier,
    )

  @strawberry.mutation
  def nicBaseOptionCreate(
    self, info: strawberry.Info, nic_base_option: NicBaseOptionCreateInput,
  ) -> NicBaseOptionCreatePayload:
    db = info.context["db"]
    return create_nic_base_option(
      db=db, input=nic_base_option,
    )
  
  @strawberry.mutation
  def nicBaseOptionsBulkCreate(
    self, info: strawberry.Info, nic_base_options: list[NicBaseOptionCreateInput],
  ) -> NicBaseOptionsBulkCreatePayload:
    db = info.context["db"]
    return bulk_create_nic_base_options(
      db=db, inputs=nic_base_options,
    )
  
  @strawberry.mutation
  def nicBaseOptionDelete(
    self, info: strawberry.Info, identifier: NicBaseOptionIdentifierInput,
  ) -> NicBaseOptionDeletePayload:
    db = info.context["db"]
    return delete_nic_base_option(
      db=db, identifier=identifier,
    )
  
  @strawberry.mutation
  def nicBaseOptionsBulkDelete(
    self, info: strawberry.Info, identifiers: list[NicBaseOptionIdentifierInput],
  ) -> NicBaseOptionsBulkDeletePayload:
    db = info.context["db"]
    return bulk_delete_nic_base_options(
      db=db, identifiers=identifiers,
    )
    
  @strawberry.mutation
  def formulaCreate(
    self, info: strawberry.Info, formula: FormulaCreateInput,
  ) -> FormulaCreatePayload:
    db = info.context["db"]
    return create_formula(
      db=db, formula=formula,
    )

  @strawberry.mutation
  def formulaDelete(
    self, info: strawberry.Info, identifier: FormulaIdentifierInput,
  ) -> FormulaDeletePayload:
    db = info.context["db"]
    return delete_formula(
      db=db, identifier=identifier,
    )

  @strawberry.mutation
  def formulaFlavoringsBulkAdd(
    self, info: strawberry.Info, identifier: FormulaIdentifierInput, flavorings: list[FormulaFlavoringInput],
  ) -> FormulaFlavoringsBulkAddPayload:
    db = info.context["db"]
    return bulk_add_formula_flavorings(
      db=db, identifier=identifier, inputs=flavorings,
    )
  
  @strawberry.mutation
  def formulaFlavoringsBulkRemove(
    self, info: strawberry.Info, flavorings: list[FormulaFlavoringIdentifierInput],
  ) -> FormulaFlavoringsBulkRemovePayload:
    db = info.context["db"]
    return bulk_remove_formula_flavorings(
      db=db, identifiers=flavorings,
    )

  @strawberry.mutation
  def formulaNicBasesBulkAdd(
   self, info: strawberry.Info, identifier: FormulaIdentifierInput, nic_bases: list[FormulaNicBaseInput],
  ) -> FormulaNicBasesBulkAddPayload:
    db = info.context["db"]
    return bulk_add_formula_nic_bases(
      db=db, identifier=identifier, inputs=nic_bases,
    )
  
  @strawberry.mutation
  def formulaNicBasesSet(
    self, info: strawberry.Info, identifier: FormulaIdentifierInput, nic_bases: list[FormulaNicBaseInput],
  ) -> FormulaNicBasesSetPayload:
    db = info.context["db"]
    return set_formula_nic_bases(
      db=db, identifier=identifier, inputs=nic_bases,
    )
  
  @strawberry.mutation
  def formulaNicBasesBulkRemove(
    self, info: strawberry.Info, nic_bases: list[FormulaNicBaseIdentifierInput],
  ) -> FormulaNicBasesBulkRemovePayload:
    db = info.context["db"]
    return bulk_remove_formula_nic_bases(
      db=db, identifiers=nic_bases,
    )

  @strawberry.mutation
  def formulaUpdate(
    self, info: strawberry.Info, identifier: FormulaIdentifierInput, formula: FormulaUpdateInput,
  ) -> FormulaUpdatePayload:
    db = info.context["db"]
    return update_formula(
      db=db, identifier=identifier, formula=formula,
    )

  @strawberry.mutation
  def productionOrderCreate(
    self, info: strawberry.Info, eliquid_identifier: EliquidIdentifierInput, production_order: ProductionOrderCreateInput,
  ) -> ProductionOrderCreatePayload:
    db = info.context["db"]
    return create_production_order(
      db=db, eliquid_identifier=eliquid_identifier, input=production_order,
    )
  
  @strawberry.mutation
  def productionOrderDelete(
    self, info: strawberry.Info, identifier: ProductionOrderIdentifierInput,
  ) -> ProductionOrderDeletePayload:
    db = info.context["db"]
    return delete_production_order(
      db=db, identifier=identifier,
    )
  
  @strawberry.mutation
  def productionOrderMarkCancelled(
    self, info: strawberry.Info, identifier: ProductionOrderIdentifierInput,
  ) -> ProductionOrderUpdatePayload:
    db = info.context["db"]
    return mark_production_order_cancelled(
      db=db, identifier=identifier,
    )

  @strawberry.mutation
  def productionOrderMarkDelivered(
    self, info: strawberry.Info, identifier: ProductionOrderIdentifierInput,
  ) -> ProductionOrderUpdatePayload:
    db = info.context["db"]
    return mark_production_order_delivered(
      db=db, identifier=identifier,
    )
    
  @strawberry.mutation
  def productionOrderMarkInProgress(
    self, info: strawberry.Info, identifier: ProductionOrderIdentifierInput,
  ) -> ProductionOrderUpdatePayload:
    db = info.context["db"]
    return mark_production_order_in_progress(
      db=db, identifier=identifier,
    )
    
  @strawberry.mutation
  def productionOrderMarkFulfilled(
    self, info: strawberry.Info, identifier: ProductionOrderIdentifierInput, fulfilled_quantity: int,
  ) -> ProductionOrderUpdatePayload:
    db = info.context["db"]
    return mark_production_order_fulfilled(
      db=db, identifier=identifier, fulfilled_quantity=fulfilled_quantity,
    )
  
  @strawberry.mutation
  def mixSessionMarkCompleted(
    self, info: strawberry.Info, identifier: MixSessionIdentifierInput,
  ) -> MixSessionUpdatePayload:
    db = info.context["db"]
    return mark_mix_session_completed(
      db=db, identifier=identifier,
    )
    
  @strawberry.mutation
  def mixSessionMarkMixed(
    self, info: strawberry.Info, identifier: MixSessionIdentifierInput,
  ) -> MixSessionUpdatePayload:
    db = info.context["db"]
    return mark_mix_session_mixed(
      db=db, identifier=identifier,
    )
  
  @strawberry.mutation
  def productionOrderSetArchived(
    self, info: strawberry.Info, identifier: ProductionOrderIdentifierInput, is_archived: bool,
  ) -> ProductionOrderUpdatePayload:
    db = info.context["db"]
    return set_production_order_archived(
      db=db, identifier=identifier, is_archived=is_archived,
    )
  
  @strawberry.mutation
  def productionOrderSetPriority(
    self, info: strawberry.Info, identifier: ProductionOrderIdentifierInput, is_priority: bool,
  ) -> ProductionOrderUpdatePayload:
    db = info.context["db"]
    return set_production_order_priority(
      db=db, identifier=identifier, is_priority=is_priority,
    )
  
  @strawberry.mutation
  def productionOrderSetOrderedQuantity(
    self, info: strawberry.Info, identifier: ProductionOrderIdentifierInput, ordered_quantity: int | None,
  ) -> ProductionOrderUpdatePayload:
    db = info.context["db"]
    return set_production_order_ordered_quantity(
      db=db, identifier=identifier, ordered_quantity=ordered_quantity,
    )
  
  @strawberry.mutation
  def locationSetArchived(
    self, info: strawberry.Info, identifier: LocationIdentifierInput, is_archived: bool,
  ) -> LocationUpdatePayload:
    db = info.context["db"]
    return set_location_archived(
      db=db, identifier=identifier, is_archived=is_archived,
    )

  @strawberry.mutation
  def productionOrderUpdate(
    self, info: strawberry.Info, identifier: ProductionOrderIdentifierInput, production_order: ProductionOrderUpdateInput,
  ) -> ProductionOrderUpdatePayload:
    db = info.context["db"]
    return update_production_order(
      db=db, identifier=identifier, input=production_order,
    )


schema = strawberry.Schema(query=Query, mutation=Mutation)