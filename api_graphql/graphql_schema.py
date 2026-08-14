import strawberry
from typing import List, Optional
from database import SessionLocal
from api_graphql.graphql_types import *
from api_graphql.resolvers import *

@strawberry.type
class Query:
  @strawberry.field
  def formulas(self) -> List[FormulaType]:
    db = SessionLocal()
    try:
      return [formula_to_type(f) for f in get_all_formulas(db)]
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
  def nicBaseOptions(self) -> List[NicBaseOptionType]:
    db = SessionLocal()
    try:
      return [nic_base_option_to_type(o) for o in get_all_nic_base_options(db)]
    finally:
      db.close()
      
  @strawberry.field
  def flavoringOptions(self) -> List[FlavoringOptionType]:
    db = SessionLocal()
    try:
      return [flavoring_option_to_type(o) for o in get_all_flavoring_options(db)]
    finally:
      db.close()


@strawberry.input
class NicProfileCreateInput:
  formula_slug: str
  name: str
  nic_base_nic_str: float
  is_old_mix: bool
  target_nic_str: float
  target_vg: float
  target_pg: float     
     
@strawberry.input
class FormulaCreateInput:
  name: str
  brand: str
  chill_type: ChillType
  nic_type: NicType
        
      
@strawberry.type
class Mutation:    
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
  def nicProfileCreate(self, input: NicProfileCreateInput) -> NicProfileCreatePayload:
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
  def formulaCreate(self, input: FormulaCreateInput) -> FormulaCreatePayload:
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
      
schema = strawberry.Schema(query=Query, mutation=Mutation) 