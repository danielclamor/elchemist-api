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
class FormulaCreateInput:
  name: str
  brand: str
  chill_type: ChillType
  nic_type: NicType
        
      
@strawberry.type
class Mutation:    
  @strawberry.mutation
  def formulaCreate(self, input: FormulaCreateInput) -> FormulaCreatePayload:
    db = SessionLocal()
    try:
      return create_formula(db, input.name, input.brand, input.chill_type, input.nic_type)
    finally:
      db.close()     
      
schema = strawberry.Schema(query=Query, mutation=Mutation) 