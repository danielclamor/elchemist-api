import strawberry
from typing import List, Optional
from database import SessionLocal
from api_graphql.graphql_types import *
from api_graphql.resolvers import *

@strawberry.type
class Query:
  @strawberry.field
  def brands(self) -> List[str]:
    db = SessionLocal()
    try:
      return get_all_brands(db=db)
    finally:
      db.close()
  
  @strawberry.field
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
    
  @strawberry.field
  def formulas(self) -> List[FormulaType]:
    db = SessionLocal()
    try:
      return [formula_to_type(f) for f in get_all_formulas(db)]
    finally:
      db.close()

  @strawberry.field
  def nicBaseOptions(self) -> List[NicBaseOptionType]:
    db = SessionLocal()
    try:
      return [nic_base_option_to_type(o) for o in get_all_nic_base_options(db)]
    finally:
      db.close()
      
  @strawberry.field
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
    self,
    input: FlavoringOptionCreateInput
  ) -> FlavoringOptionCreatePayload:
    db = SessionLocal()
    try:
      flavoring_option_slug = make_slug(input.name)
      
      flavoring_option = get_flavoring_option(
        db=db,
        flavoring_option_slug=flavoring_option_slug
      )
      
      if flavoring_option:
        return FlavoringOptionCreatePayload(
          flavoring_option=flavoring_option,
          feedback=Feedback(
            status=FeedbackStatus.CANCELLED,
            message=f"Flavoring option {input.name} already exists"
          )
        )
      
      flavoring_option = create_flavoring_option(
        db=db,
        flavoring_option_name=input.name,
        is_vg=input.is_vg
      )
      
      return FlavoringOptionCreatePayload(
        flavoring_option=flavoring_option,
        feedback=Feedback(
          status=FeedbackStatus.SUCCESS,
          message=None
        )
      )
    finally:
      db.close()  
  
  @strawberry.mutation
  def formulaCreate(
    self, 
    input: FormulaCreateInput
  ) -> FormulaCreatePayload:
    db = SessionLocal()
    try:
      return create_formula(
        db=db, 
        name=input.name, 
        brand=input.brand, 
        chill_type=input.chill_type, 
        nic_type=input.nic_type,
        )
    finally:
      db.close()
  
  @strawberry.mutation
  def formulaDelete(
    self,
    formula_slug: str
  ) -> FormulaDeletePayload:
    db = SessionLocal()
    try:
      return delete_formula(
        db=db,
        formula_slug=formula_slug
      )
    finally:
      db.close()
      
  @strawberry.mutation
  def formulaUpdate(
    self,
    input: FormulaUpdateInput
  ) -> FormulaUpdatePayload:
    db = SessionLocal()
    try:
      return update_formula(
        db=db,
        input=input
      )
    finally:
      db.close()
  
  @strawberry.mutation
  def nicBaseOptionCreate(
    self,
    input: NicBaseOptionCreateInput
  ) -> NicBaseOptionCreatePayload:
    db = SessionLocal()
    try:
      nic_base_option = get_nic_base_option(
        db=db,
        nic_base_option_code=input.code
      )
      
      if nic_base_option:
        return NicBaseOptionCreatePayload(
          nic_base_option=nic_base_option,
          feedback=Feedback(
            status=FeedbackStatus.CANCELLED,
            message=f"Nic base option {input.code} already exists"
          )
        )
      
      nic_base_option = create_nic_base_option(
        db=db,
        nic_base_option_code=input.code,
        nic_base_option_name=input.name,
        is_vg=input.is_vg
      )
      
      return NicBaseOptionCreatePayload(
        nic_base_option=nic_base_option,
        feedback=Feedback(
          status=FeedbackStatus.SUCCESS,
          message=None,
        )
      )
    finally:
      db.close()

  @strawberry.mutation
  def nicProfileAddFlavoring(
    self, 
    nic_profile_slug: str, 
    flavoring_option_name: str, 
    ratio: float, 
    is_vg: bool | None = None
  ) -> NicProfileAddFlavoringPayload:
    db = SessionLocal()
    try:
      return add_nic_profile_flavoring(
        db=db,
        nic_profile_slug=nic_profile_slug,
        flavoring_option_name=flavoring_option_name,
        is_vg=is_vg,
        ratio=ratio,
      )
    finally:
      db.close()

  @strawberry.mutation
  def nicProfileAddNicBase(
    self, 
    nic_profile_slug: str, 
    nic_base_option_code: str, 
    ratio: float, 
    nic_base_option_name: str | None = None, 
    is_vg: bool | None = None
  ) -> NicProfileAddNicBasePayload:
    db = SessionLocal()
    try:
      return add_nic_profile_nic_base(
        db=db,
        nic_profile_slug=nic_profile_slug,
        nic_base_option_code=nic_base_option_code,
        ratio=ratio,
        nic_base_option_name=nic_base_option_name,
        is_vg=is_vg,
      )
    finally:
      db.close()

  @strawberry.mutation
  def nicProfileCreate(
    self, 
    input: NicProfileCreateInput
    ) -> NicProfileCreatePayload:
    db = SessionLocal()
    try:
      return create_nic_profile(
        db=db, 
        formula_slug=input.formula_slug, 
        name=input.name,
        nic_base_str=input.nic_base_nic_str,
        is_old_mix=input.is_old_mix,
        target_nic_str=input.target_nic_str,
        target_vg=input.target_vg,
        target_pg=input.target_pg,
        )
    finally:
      db.close()

  @strawberry.mutation
  def nicProfileDelete(
    self,
    input: NicProfileDeleteInput
  ) -> NicProfileDeletePayload:
    db = SessionLocal()
    try:
      return delete_nic_profile(
        db=db,
        nic_profile_slug=input.nic_profile_slug
      )
    finally:
      db.close()

schema = strawberry.Schema(query=Query, mutation=Mutation) 