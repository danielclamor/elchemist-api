from graphql import GraphQLError
import strawberry
from strawberry import relay
from typing import List, Optional
from database import SessionLocal

from api_graphql.types.enums import FeedbackStatus
from api_graphql.types.feedback import Feedback
from api_graphql.types.brand import BrandEdge, BrandConnection
from api_graphql.types.eliquid import EliquidType
from api_graphql.types.flavoring import (
  FlavoringOptionType,
  FlavoringOptionCreateInput,
  FlavoringOptionCreatePayload,
)
from api_graphql.types.formula import (
  FormulaType,
  FormulaCreateInput,
  FormulaCreatePayload,
  FormulaDeleteInput,
  FormulaDeletePayload,
  FormulaUpdateIdentifier,
  FormulaUpdateInput,
  FormulaUpdatePayload,
)
from api_graphql.types.nic_base import (
  NicBaseOptionType,
  NicBaseOptionCreateInput,
  NicBaseOptionCreatePayload,
)
from api_graphql.types.nic_profile import (
  NicProfileType,
  NicProfileAddFlavoringInput,
  NicProfileAddFlavoringPayload,
  NicProfileAddNicBaseInput,
  NicProfileAddNicBasePayload,
  NicProfileCreateInput,
  NicProfileCreatePayload,
  NicProfileDeleteInput,
  NicProfileDeletePayload,
  NicProfileUpdateIdentifier,
  NicProfileUpdateInput,
  NicProfileUpdatePayload,
)

from api_graphql.resolvers import (
  get_all_brands,
  get_all_eliquids,
  get_all_flavoring_options,
  get_all_formulas,
  get_all_nic_base_options,
  get_all_nic_profiles,
  get_formula,
  get_flavoring_option,
  get_nic_base_option,
  make_slug,
  bulk_add_nic_profile_flavorings,
  bulk_add_nic_profile_nic_bases,
  create_flavoring_option,
  create_formula,
  create_nic_base_option,
  create_nic_profile,
  delete_formula,
  delete_nic_profile,
  update_formula,
  update_nic_profile,
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

  @relay.connection(relay.ListConnection[FlavoringOptionType])
  def flavoringOptions(
    self, info: strawberry.Info
  ) -> List[FlavoringOptionType]:
    db = info.context["db"]
    return [FlavoringOptionType.from_model(o) for o in get_all_flavoring_options(db)]

  @strawberry.field
  def formula(
    self, info: strawberry.Info, slug: str
  ) -> Optional[FormulaType]:
    db = info.context["db"]
    f = get_formula(db=db, formula_slug=slug)
    return FormulaType.from_model(f) if f else None

  @relay.connection(relay.ListConnection[FormulaType])
  def formulas(
    self, info: strawberry.Info
  ) -> List[FormulaType]:
    db = info.context["db"]
    return [FormulaType.from_model(f) for f in get_all_formulas(db)]

  @relay.connection(relay.ListConnection[NicBaseOptionType])
  def nicBaseOptions(
    self, info: strawberry.Info
  ) -> List[NicBaseOptionType]:
    db = info.context["db"]
    return [NicBaseOptionType.from_model(o) for o in get_all_nic_base_options(db)]

  @relay.connection(relay.ListConnection[NicProfileType])
  def nicProfiles(
    self, info: strawberry.Info
  ) -> List[NicProfileType]:
    db = info.context["db"]
    return [NicProfileType.from_model(p) for p in get_all_nic_profiles(db)]


@strawberry.type
class Mutation:
  @strawberry.mutation
  def flavoringOptionCreate(
    self, info: strawberry.Info, flavoring_option: FlavoringOptionCreateInput
  ) -> FlavoringOptionCreatePayload:
    db = info.context["db"]
    flavoring_option_slug = make_slug(flavoring_option.name)

    existing = get_flavoring_option(
      db=db, flavoring_option_slug=flavoring_option_slug
    )

    if existing:
      return FlavoringOptionCreatePayload(
        flavoring_option=FlavoringOptionType.from_model(existing),
        feedback=Feedback(
          status=FeedbackStatus.CANCELLED,
          message=f"Flavoring option {flavoring_option.name} already exists",
        ),
      )

    created = create_flavoring_option(db=db, flavoring_option=flavoring_option)

    return FlavoringOptionCreatePayload(
      flavoring_option=FlavoringOptionType.from_model(created),
      feedback=Feedback(status=FeedbackStatus.SUCCESS, message=None),
    )

  @strawberry.mutation
  def formulaCreate(
    self, info: strawberry.Info, formula: FormulaCreateInput
  ) -> FormulaCreatePayload:
    db = info.context["db"]
    return create_formula(db=db, formula=formula)

  @strawberry.mutation
  def formulaDelete(
    self, info: strawberry.Info, input: FormulaDeleteInput
  ) -> FormulaDeletePayload:
    db = info.context["db"]
    return delete_formula(db=db, input=input)

  @strawberry.mutation
  def formulaUpdate(
    self, info: strawberry.Info, identifier: FormulaUpdateIdentifier, input: FormulaUpdateInput
  ) -> FormulaUpdatePayload:
    db = info.context["db"]
    return update_formula(db=db, identifier=identifier, formula=input)

  @strawberry.mutation
  def nicBaseOptionCreate(
    self, info: strawberry.Info, nic_base_option: NicBaseOptionCreateInput
  ) -> NicBaseOptionCreatePayload:
    db = info.context["db"]
    existing = get_nic_base_option(
      db=db, nic_base_option_code=nic_base_option.code
    )

    if existing:
      return NicBaseOptionCreatePayload(
        nic_base_option=NicBaseOptionType.from_model(existing),
        feedback=Feedback(
          status=FeedbackStatus.CANCELLED,
          message=f"Nic base option {nic_base_option.code} already exists",
        ),
      )

    created = create_nic_base_option(db=db, nic_base_option=nic_base_option)

    return NicBaseOptionCreatePayload(
      nic_base_option=NicBaseOptionType.from_model(created),
      feedback=Feedback(status=FeedbackStatus.SUCCESS, message=None),
    )

  @strawberry.mutation
  def nicProfileBulkAddFlavoring(
      self, info: strawberry.Info, nic_profile_slug: str, flavorings: List[NicProfileAddFlavoringInput]
  ) -> NicProfileAddFlavoringPayload:
    db = info.context["db"]
    return bulk_add_nic_profile_flavorings(
      db=db, nic_profile_slug=nic_profile_slug, flavorings=flavorings
    )

  @strawberry.mutation
  def nicProfileBulkAddNicBases(
      self, info: strawberry.Info, nic_profile_slug: str, nic_bases: List[NicProfileAddNicBaseInput]
  ) -> NicProfileAddNicBasePayload:
    db = info.context["db"]
    return bulk_add_nic_profile_nic_bases(
      db=db, nic_profile_slug=nic_profile_slug, nic_bases=nic_bases
    )
    
  @strawberry.mutation
  def nicProfileCreate(
      self, info: strawberry.Info, formula_slug: str, nic_profile: NicProfileCreateInput
  ) -> NicProfileCreatePayload:
    db = info.context["db"]
    return create_nic_profile(
      db=db, formula_slug=formula_slug, nic_profile=nic_profile
    )

  @strawberry.mutation
  def nicProfileDelete(
    self, info: strawberry.Info, input: NicProfileDeleteInput
  ) -> NicProfileDeletePayload:
    db = info.context["db"]
    return delete_nic_profile(db=db, input=input)

  @strawberry.mutation
  def nicProfileUpdate(
      self, info: strawberry.Info, identifier: NicProfileUpdateIdentifier, nic_profile: NicProfileUpdateInput
  ) -> NicProfileUpdatePayload:
    db = info.context["db"]
    return update_nic_profile(db=db, identifier=identifier, nic_profile=nic_profile)


schema = strawberry.Schema(query=Query, mutation=Mutation)