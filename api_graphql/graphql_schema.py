from graphql import GraphQLError
import strawberry
from strawberry import relay
from typing import Any, List, Optional
from database import SessionLocal
from api_graphql.graphql_types import *
from api_graphql.resolvers import *

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
    BrandEdge(cursor=strawberry.relay.to_base64("brandindex", str(start + i)), node=b)
    for i, b in enumerate(page)
  ]

  return BrandConnection(
    edges=edges,
    page_info=strawberry.relay.PageInfo(
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
    self, after: Optional[str] = None, before: Optional[str] = None, first: Optional[int] = None, last: Optional[int] = None
  ) -> BrandConnection:
    db = SessionLocal()
    try:
      return _paginate_brands(get_all_brands(db=db), after, before, first, last)
    finally:
      db.close()

  @relay.connection(relay.ListConnection[EliquidType])
  def eliquids(self) -> List[EliquidType]:
    db = SessionLocal()
    try:
      return [eliquid_to_type(e) for e in get_all_eliquids(db)]
    finally:
      db.close()

  @relay.connection(relay.ListConnection[FlavoringOptionType])
  def flavoringOptions(self) -> List[FlavoringOptionType]:
    db = SessionLocal()
    try:
      return [flavoring_option_to_type(o) for o in get_all_flavoring_options(db)]
    finally:
      db.close()

  @strawberry.field
  def formula(self, slug: str) -> Optional[FormulaType]:
    db = SessionLocal()
    try:
      f = db.query(models.Formula).filter(models.Formula.slug == slug).first()
      return formula_to_type(f) if f else None
    finally:
      db.close()

  @relay.connection(relay.ListConnection[FormulaType])
  def formulas(self) -> List[FormulaType]:
    db = SessionLocal()
    try:
      return [formula_to_type(f) for f in get_all_formulas(db)]
    finally:
      db.close()

  @relay.connection(relay.ListConnection[NicBaseOptionType])
  def nicBaseOptions(self) -> List[NicBaseOptionType]:
    db = SessionLocal()
    try:
      return [nic_base_option_to_type(o) for o in get_all_nic_base_options(db)]
    finally:
      db.close()

  @relay.connection(relay.ListConnection[NicProfileType])
  def nicProfiles(self) -> List[NicProfileType]:
    db = SessionLocal()
    try:
      return [nic_profile_to_type(p) for p in get_all_nic_profiles(db)]
    finally:
      db.close()


@strawberry.type
class Mutation:
  @strawberry.mutation
  def flavoringOptionCreate(
    self, flavoring_option: FlavoringOptionCreateInput
  ) -> FlavoringOptionCreatePayload:
    db = SessionLocal()
    try:
      flavoring_option_slug = make_slug(flavoring_option.name)

      existing = get_flavoring_option(
        db=db, flavoring_option_slug=flavoring_option_slug
      )

      if existing:
        return FlavoringOptionCreatePayload(
          flavoring_option=existing,
          feedback=Feedback(
            status=FeedbackStatus.CANCELLED,
            message=f"Flavoring option {flavoring_option.name} already exists",
          ),
        )

      created = create_flavoring_option(
        db=db,
        flavoring_option_name=flavoring_option.name,
        is_vg=flavoring_option.is_vg,
      )

      return FlavoringOptionCreatePayload(
        flavoring_option=created,
        feedback=Feedback(status=FeedbackStatus.SUCCESS, message=None),
      )
    finally:
      db.close()

  @strawberry.mutation
  def formulaCreate(self, formula: FormulaCreateInput) -> FormulaCreatePayload:
    db = SessionLocal()
    try:
      return create_formula(db=db, formula=formula)
    finally:
      db.close()

  @strawberry.mutation
  def formulaDelete(self, formula_slug: str) -> FormulaDeletePayload:
    db = SessionLocal()
    try:
      return delete_formula(db=db, formula_slug=formula_slug)
    finally:
      db.close()

  @strawberry.mutation
  def formulaUpdate(
    self, identifier: FormulaUpdateIdentifier, input: FormulaUpdateInput
  ) -> FormulaUpdatePayload:
    db = SessionLocal()
    try:
      return update_formula(db=db, identifier=identifier, formula=input)
    finally:
      db.close()

  @strawberry.mutation
  def nicBaseOptionCreate(
    self, nic_base_option: NicBaseOptionCreateInput
  ) -> NicBaseOptionCreatePayload:
    db = SessionLocal()
    try:
      existing = get_nic_base_option(
        db=db, nic_base_option_code=nic_base_option.code
      )

      if existing:
        return NicBaseOptionCreatePayload(
          nic_base_option=existing,
          feedback=Feedback(
            status=FeedbackStatus.CANCELLED,
            message=f"Nic base option {nic_base_option.code} already exists",
          ),
        )

      created = create_nic_base_option(db=db, nic_base_option=nic_base_option)

      return NicBaseOptionCreatePayload(
        nic_base_option=created,
        feedback=Feedback(status=FeedbackStatus.SUCCESS, message=None),
      )
    finally:
      db.close()

  @strawberry.mutation
  def nicProfileBulkAddFlavoring(
      self, nic_profile_slug: str, flavorings: List[NicProfileAddFlavoringInput]
  ) -> NicProfileAddFlavoringPayload:
    db = SessionLocal()
    try:
      return bulk_add_nic_profile_flavorings(
        db=db, nic_profile_slug=nic_profile_slug, flavorings=flavorings
      )
    finally:
      db.close()

  @strawberry.mutation
  def nicProfileBulkAddNicBases(
      self, nic_profile_slug: str, nic_bases: List[NicProfileAddNicBaseInput]
  ) -> NicProfileAddNicBasePayload:
    db = SessionLocal()
    try:
      return bulk_add_nic_profile_nic_bases(
        db=db, nic_profile_slug=nic_profile_slug, nic_bases=nic_bases
      )
    finally:
      db.close()

  @strawberry.mutation
  def nicProfileCreate(
      self, formula_slug: str, nic_profile: NicProfileCreateInput
  ) -> NicProfileCreatePayload:
    db = SessionLocal()
    try:
      return create_nic_profile(
        db=db, formula_slug=formula_slug, nic_profile=nic_profile
      )
    finally:
      db.close()

  @strawberry.mutation
  def nicProfileDelete(self, input: NicProfileDeleteInput) -> NicProfileDeletePayload:
    db = SessionLocal()
    try:
      return delete_nic_profile(db=db, nic_profile_slug=input.slug)
    finally:
      db.close()

  @strawberry.mutation
  def nicProfileUpdate(
      self, identifier: NicProfileUpdateIdentifier, nic_profile: NicProfileUpdateInput
  ) -> NicProfileUpdatePayload:
    db = SessionLocal()
    try:
      return update_nic_profile(db=db, identifier=identifier, nic_profile=nic_profile)
    finally:
      db.close()


schema = strawberry.Schema(query=Query, mutation=Mutation)