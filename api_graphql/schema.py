from graphql import GraphQLError
import strawberry
from strawberry import relay
from typing import List, Optional

from api_graphql.types.feedback import Feedback, FeedbackStatus
from api_graphql.types.brand import BrandEdge, BrandConnection
from api_graphql.types.eliquid import (
  EliquidType,
  EliquidCreateInput, 
  EliquidCreatePayload,
  EliquidDeletePayload,
  EliquidIdentifier,
  EliquidUpdateInput, 
  EliquidUpdatePayload,
)
from api_graphql.types.flavoring_option import (
  FlavoringOptionsBulkDeletePayload,
  FlavoringOptionDeletePayload,
  FlavoringOptionType,
  FlavoringOptionIdentifierInput,
  FlavoringOptionCreateInput,
  FlavoringOptionCreatePayload,
  FlavoringOptionsBulkCreatePayload,
)
from api_graphql.types.formula import (
  FormulaType,
  FormulaIdentifierInput,
  FormulaCreateInput,
  FormulaCreatePayload,
  FormulaDeletePayload,
  FormulaUpdateInput,
  FormulaUpdatePayload,
)
from api_graphql.types.nic_base_option import (
  NicBaseOptionType,
  NicBaseOptionIdentifierInput,
  NicBaseOptionCreateInput,
  NicBaseOptionCreatePayload,
  NicBaseOptionsBulkCreatePayload,
  NicBaseOptionDeletePayload,
  NicBaseOptionsBulkDeletePayload,
)
from api_graphql.types.nic_profile import (
  NicProfileType,
  NicProfileIdentifierInput,
  NicProfileCreateInput,
  NicProfileCreatePayload,
  NicProfileDeletePayload,
  NicProfileUpdateInput,
  NicProfileUpdatePayload,
  NicProfileFlavoringInput,
  NicProfileFlavoringIdentifierInput,
  NicProfileFlavoringsBulkAddPayload,
  NicProfileFlavoringsBulkRemovePayload,
  NicProfileNicBaseInput,
  NicProfileNicBaseIdentifierInput,
  NicProfileNicBasesBulkAddPayload,
  NicProfileNicBasesBulkRemovePayload,
)

from api_graphql.types.production_order import (
  ProductionOrderType,
  ProductionOrderCreateInput,
  ProductionOrderCreatePayload,
  ProductionOrderDeleteInput,
  ProductionOrderDeletePayload,
  ProductionOrderUpdateIdentifier,
  ProductionOrderUpdateInput,
  ProductionOrderUpdatePayload,
)

from api_graphql.resolvers.brand import (
  get_all_brands,
)

from api_graphql.resolvers.eliquid import (
  create_eliquid,
  delete_eliquid,
  get_all_eliquids,
  set_eliquid_nic_profile,
  update_eliquid,
)

from api_graphql.resolvers.formula import (
  create_formula,
  delete_formula,
  get_all_formulas,
  get_formula,
  update_formula,
)

from api_graphql.resolvers.nic_profile import (
  bulk_add_nic_profile_flavorings,
  bulk_add_nic_profile_nic_bases,
  bulk_remove_nic_profile_flavorings,
  bulk_remove_nic_profile_nic_bases,
  create_nic_profile,
  delete_nic_profile,
  get_all_nic_profiles,
  get_nic_profile,
  update_nic_profile,
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

from api_graphql.resolvers.production_order import (
  create_production_order,
  delete_production_order,
  get_all_production_orders,
  get_production_order,
  update_production_order,
)

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
  last: Optional[int]
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
    self, info: strawberry.Info, after: Optional[str] = None, before: Optional[str] = None, first: Optional[int] = None, last: Optional[int] = None
  ) -> BrandConnection:
    db = info.context["db"]
    return _paginate_brands(get_all_brands(db=db), after, before, first, last)

  @relay.connection(relay.ListConnection[EliquidType])
  def eliquids(
    self, info: strawberry.Info
  ) -> List[EliquidType]:
    db = info.context["db"]
    return [EliquidType.from_model(e) for e in get_all_eliquids(db)]
  
  @strawberry.field
  def flavoringOption(
    self, info: strawberry.Info, identifier: FlavoringOptionIdentifierInput
  ) -> Optional[FlavoringOptionType]:
    db = info.context["db"]
    o = get_flavoring_option(db=db, identifier=identifier)
    return FlavoringOptionType.from_model(o) if o else None

  @relay.connection(relay.ListConnection[FlavoringOptionType])
  def flavoringOptions(
    self, info: strawberry.Info
  ) -> List[FlavoringOptionType]:
    db = info.context["db"]
    return [FlavoringOptionType.from_model(o) for o in get_all_flavoring_options(db)]

  @strawberry.field
  def formula(
    self, info: strawberry.Info, identifier: FormulaIdentifierInput
  ) -> Optional[FormulaType]:
    db = info.context["db"]
    f = get_formula(db=db, identifier=identifier)
    return FormulaType.from_model(f) if f else None

  @relay.connection(relay.ListConnection[FormulaType])
  def formulas(
    self, info: strawberry.Info
  ) -> List[FormulaType]:
    db = info.context["db"]
    return [FormulaType.from_model(f) for f in get_all_formulas(db)]
  
  @strawberry.field
  def nicBaseOption(
    self, info: strawberry.Info, identifier: NicBaseOptionIdentifierInput
  ) -> Optional[NicBaseOptionType]:
    db = info.context["db"]
    o = get_nic_base_option(db=db, identifier=identifier)
    return NicBaseOptionType.from_model(o) if o else None

  @relay.connection(relay.ListConnection[NicBaseOptionType])
  def nicBaseOptions(
    self, info: strawberry.Info
  ) -> List[NicBaseOptionType]:
    db = info.context["db"]
    return [NicBaseOptionType.from_model(o) for o in get_all_nic_base_options(db)]

  @strawberry.field
  def nicProfile(
    self, info: strawberry.Info, identifier: NicProfileIdentifierInput
  ) -> Optional[NicProfileType]:
    db = info.context["db"]
    p = get_nic_profile(db=db, identifier=identifier)
    return NicProfileType.from_model(p) if p else None
  
  @relay.connection(relay.ListConnection[NicProfileType])
  def nicProfiles(
    self, info: strawberry.Info
  ) -> List[NicProfileType]:
    db = info.context["db"]
    return [NicProfileType.from_model(p) for p in get_all_nic_profiles(db)]
  
  @strawberry.field
  def productionOrder(
    self, info: strawberry.Info, order_number: str,
  ) -> ProductionOrderType:
    db = info.context["db"]
    return ProductionOrderType.from_model(get_production_order(db, order_number=order_number))
  
  @relay.connection(relay.ListConnection[ProductionOrderType])
  def productionOrders(
    self, info: strawberry.Info
  ) -> List[ProductionOrderType]:
    db = info.context["db"]
    return [ProductionOrderType.from_model(po) for po in get_all_production_orders(db)]


@strawberry.type
class Mutation:
  @strawberry.mutation
  def eliquidCreate(
    self, info: strawberry.Info, eliquid: EliquidCreateInput
  ) -> EliquidCreatePayload:
    db = info.context["db"]
    return create_eliquid(
      db=db, input=eliquid
    )
  
  @strawberry.mutation
  def eliquidDelete(
    self, info: strawberry.Info, identifier: EliquidIdentifier
  ) -> EliquidDeletePayload:
    db = info.context["db"]
    return delete_eliquid(
      db=db, identifier=identifier
    )
  
  @strawberry.mutation
  def eliquidUpdate(
    self, info: strawberry.Info, identifier: EliquidIdentifier, eliquid: EliquidUpdateInput
  ) -> EliquidUpdatePayload:
    db = info.context["db"]
    return update_eliquid(
      db=db, identifier=identifier, input=eliquid
    )
  
  @strawberry.mutation
  def eliquidNicProfileSet(
    self, info: strawberry.Info, identifier: EliquidIdentifier, nic_profile_id: relay.GlobalID | None
  ) -> EliquidUpdatePayload:
    db = info.context["db"]
    return set_eliquid_nic_profile(
      db=db, identifier=identifier, nic_profile_id=nic_profile_id
    )
  
  @strawberry.mutation
  def flavoringOptionCreate(
    self, info: strawberry.Info, flavoring_option: FlavoringOptionCreateInput
  ) -> FlavoringOptionCreatePayload:
    db = info.context["db"]
    return create_flavoring_option(
      db=db, input=flavoring_option
    )
  
  @strawberry.mutation
  def flavoringOptionsBulkCreate(
    self, info: strawberry.Info, flavoring_options: list[FlavoringOptionCreateInput]
  ) -> FlavoringOptionsBulkCreatePayload:
    db = info.context["db"]
    return bulk_create_flavoring_options(
      db=db, inputs=flavoring_options
    )
  
  @strawberry.mutation
  def flavoringOptionDelete(
    self, info: strawberry.Info, identifier: FlavoringOptionIdentifierInput
  ) -> FlavoringOptionDeletePayload:
    db = info.context["db"]
    return delete_flavoring_option(
      db=db, identifier=identifier
    )
  
  @strawberry.mutation
  def flavoringOptionsBulkDelete(
    self, info: strawberry.Info, identifiers: list[FlavoringOptionIdentifierInput]
  ) -> FlavoringOptionsBulkDeletePayload:
    db = info.context["db"]
    return bulk_delete_flavoring_options(
      db=db, identifiers=identifiers
    )

  @strawberry.mutation
  def formulaCreate(
    self, info: strawberry.Info, formula: FormulaCreateInput
  ) -> FormulaCreatePayload:
    db = info.context["db"]
    return create_formula(
      db=db, input=formula
    )

  @strawberry.mutation
  def formulaDelete(
    self, info: strawberry.Info, identifier: FormulaIdentifierInput
  ) -> FormulaDeletePayload:
    db = info.context["db"]
    return delete_formula(
      db=db, identifier=identifier
    )

  @strawberry.mutation
  def formulaUpdate(
    self, info: strawberry.Info, identifier: FormulaIdentifierInput, formula: FormulaUpdateInput
  ) -> FormulaUpdatePayload:
    db = info.context["db"]
    return update_formula(
      db=db, identifier=identifier, input=formula
    )

  @strawberry.mutation
  def nicBaseOptionCreate(
    self, info: strawberry.Info, nic_base_option: NicBaseOptionCreateInput
  ) -> NicBaseOptionCreatePayload:
    db = info.context["db"]
    return create_nic_base_option(
      db=db, input=nic_base_option
    )
  
  @strawberry.mutation
  def nicBaseOptionsBulkCreate(
    self, info: strawberry.Info, nic_base_options: list[NicBaseOptionCreateInput]
  ) -> NicBaseOptionsBulkCreatePayload:
    db = info.context["db"]
    return bulk_create_nic_base_options(
      db=db, inputs=nic_base_options
    )
  
  @strawberry.mutation
  def nicBaseOptionDelete(
    self, info: strawberry.Info, identifier: NicBaseOptionIdentifierInput
  ) -> NicBaseOptionDeletePayload:
    db = info.context["db"]
    return delete_nic_base_option(
      db=db, identifier=identifier
    )
  
  @strawberry.mutation
  def nicBaseOptionsBulkDelete(
    self, info: strawberry.Info, identifiers: list[NicBaseOptionIdentifierInput]
  ) -> NicBaseOptionsBulkDeletePayload:
    db = info.context["db"]
    return bulk_delete_nic_base_options(
      db=db, identifiers=identifiers
    )
    
  @strawberry.mutation
  def nicProfileCreate(
    self, info: strawberry.Info, formula_identifier: FormulaIdentifierInput, nic_profile: NicProfileCreateInput
  ) -> NicProfileCreatePayload:
    db = info.context["db"]
    return create_nic_profile(
      db=db, formula_identifier=formula_identifier, nic_profile=nic_profile
    )

  @strawberry.mutation
  def nicProfileDelete(
    self, info: strawberry.Info, identifier: NicProfileIdentifierInput
  ) -> NicProfileDeletePayload:
    db = info.context["db"]
    return delete_nic_profile(
      db=db, identifier=identifier
    )

  @strawberry.mutation
  def nicProfileFlavoringsBulkAdd(
    self, info: strawberry.Info, identifier: NicProfileIdentifierInput, flavorings: list[NicProfileFlavoringInput]
  ) -> NicProfileFlavoringsBulkAddPayload:
    db = info.context["db"]
    return bulk_add_nic_profile_flavorings(
      db=db, identifier=identifier, inputs=flavorings
    )
  
  @strawberry.mutation
  def nicProfileFlavoringsBulkRemove(
    self, info: strawberry.Info, flavorings: list[NicProfileFlavoringIdentifierInput]
  ) -> NicProfileFlavoringsBulkRemovePayload:
    db = info.context["db"]
    return bulk_remove_nic_profile_flavorings(
      db=db, identifiers=flavorings
    )

  @strawberry.mutation
  def nicProfileNicBasesBulkAdd(
   self, info: strawberry.Info, identifier: NicProfileIdentifierInput, nic_bases: list[NicProfileNicBaseInput]
  ) -> NicProfileNicBasesBulkAddPayload:
    db = info.context["db"]
    return bulk_add_nic_profile_nic_bases(
      db=db, identifier=identifier, inputs=nic_bases
    )
  
  @strawberry.mutation
  def nicProfileNicBasesBulkRemove(
    self, info: strawberry.Info, nic_bases: list[NicProfileNicBaseIdentifierInput]
  ) -> NicProfileNicBasesBulkRemovePayload:
    db = info.context["db"]
    return bulk_remove_nic_profile_nic_bases(
      db=db, identifiers=nic_bases
    )

  @strawberry.mutation
  def nicProfileUpdate(
    self, info: strawberry.Info, identifier: NicProfileIdentifierInput, nic_profile: NicProfileUpdateInput
  ) -> NicProfileUpdatePayload:
    db = info.context["db"]
    return update_nic_profile(
      db=db, identifier=identifier, nic_profile=nic_profile
    )

  @strawberry.mutation
  def productionOrderCreate(
    self, info: strawberry.Info, production_order: ProductionOrderCreateInput
  ) -> ProductionOrderCreatePayload:
    db = info.context["db"]
    return create_production_order(
      db=db, input=production_order
    )
  
  @strawberry.mutation
  def productionOrderDelete(
    self, info: strawberry.Info, input: ProductionOrderDeleteInput
  ) -> ProductionOrderDeletePayload:
    db = info.context["db"]
    return delete_production_order(
      db=db, input=input
    )
  
  @strawberry.mutation
  def productionOrderUpdate(
    self, info: strawberry.Info, identifier: ProductionOrderUpdateIdentifier, production_order: ProductionOrderUpdateInput
  ) -> ProductionOrderUpdatePayload:
    db = info.context["db"]
    return update_production_order(
      db=db, identifier=identifier, input=production_order
    )


schema = strawberry.Schema(query=Query, mutation=Mutation)