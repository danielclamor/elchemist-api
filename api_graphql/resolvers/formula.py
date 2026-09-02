from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import strawberry

from .utils import generate_slug

from models import Formula, ChillType, NicType

from api_graphql.types.feedback import Feedback, FeedbackStatus

from api_graphql.types.formula import (
  FormulaType, 
  FormulaCreatePayload, 
  FormulaDeletePayload, 
  FormulaUpdatePayload
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from api_graphql.types.formula import (
    FormulaIdentifierInput,
    FormulaCreateInput,
    FormulaUpdateInput,
  )

# Queries
def get_all_formulas(db: Session) -> list[Formula]:
  return (
    db.scalars(select(Formula))
    .unique()
    .all()
  )
  
def get_formula(db: Session, identifier: "FormulaIdentifierInput") -> Formula:
  return (
    db.scalar(select(Formula).where(identifier.query_condition))
  )


# Mutations
def create_formula(db: Session, input: "FormulaCreateInput") -> FormulaCreatePayload:
  slug = generate_slug(string=input.name)

  existing = db.scalar(select(Formula).where(Formula.slug == slug))
  
  if existing is not None:
    return FormulaCreatePayload(
      formula=FormulaType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Formula {slug} already exists",
      )
    )

  formula = Formula(
    slug=slug,
    name=input.name,
    brand=input.brand,
    chill_type=ChillType[input.chill_type.name],
    nic_type=NicType[input.nic_type.name],
  )

  db.add(formula)
  db.commit()
  db.refresh(formula)
  
  return FormulaCreatePayload(
    formula=FormulaType.from_model(formula),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def delete_formula(db: Session, identifier: "FormulaIdentifierInput") -> FormulaDeletePayload:
  formula = get_formula(db=db, identifier=identifier)
  
  if formula is None:
    return FormulaDeletePayload(
      deleted_slug=None,
      deleted_name=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Formula {identifier.provided} not found."
      )
    )
  
  slug = formula.slug
  name = formula.name

  db.delete(formula)
  db.commit()

  return FormulaDeletePayload(
    deleted_slug=slug,
    deleted_name=name,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )
  
def update_formula(db: Session, identifier: "FormulaIdentifierInput", input: "FormulaUpdateInput") -> FormulaUpdatePayload:
  formula = get_formula(db=db, identifier=identifier)
  
  if formula is None:
    return FormulaUpdatePayload(
      formula=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Formula not found."
      )
    )
  
  updated_columns = []
  
  for attr, value in vars(input).items():
    current = getattr(formula, attr, None)
    
    if value is strawberry.UNSET:
      continue
    
    if isinstance(value, Enum):
      value = value.name
      current = current.name
      
    if value != current:
      setattr(formula, attr, value)
      db.flush()
      updated_columns.append(f"{attr}")
      
  if len(updated_columns) == 0:
    message = "Nothing to update"
  else:
    db.commit()
    db.refresh(formula)
    message = f"Updated {", ".join(updated_columns)}"

  db.commit()
  db.refresh(formula)
  
  return FormulaUpdatePayload(
    formula=FormulaType.from_model(formula),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=message
    )
  )