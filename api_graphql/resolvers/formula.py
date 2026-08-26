from sqlalchemy.orm import Session
from sqlalchemy import select
import models

from .utils import generate_slug

from api_graphql.types.enums import FeedbackStatus
from api_graphql.types.feedback import Feedback
from api_graphql.types.formula import FormulaType, FormulaCreatePayload, FormulaDeletePayload, FormulaUpdatePayload

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from api_graphql.types.formula import (
    FormulaCreateInput,
    FormulaDeleteInput,
    FormulaUpdateIdentifier,
    FormulaUpdateInput,
  )

# Queries
def get_all_formulas(db: Session) -> list[models.Formula]:
  return (
    db.scalars(select(models.Formula))
    .unique()
    .all()
  )
  
def get_formula(db: Session, formula_slug: str) -> models.Formula:
  return (
    db.scalar(select(models.Formula).where(models.Formula.slug == formula_slug))
  )
  

# Mutations
def create_formula(db: Session, formula: "FormulaCreateInput") -> FormulaCreatePayload:
  slug = generate_slug(string=formula.name)

  existing = db.scalar(select(models.Formula).where(models.Formula.slug == slug))
  if existing:
    return FormulaCreatePayload(
      formula=FormulaType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Formula {slug} already exists",
      )
    )

  formula = models.Formula(
    slug=slug,
    name=formula.name,
    brand=formula.brand,
    chill_type=models.ChillType[formula.chill_type.name],
    nic_type=models.NicType[formula.nic_type.name],
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

def delete_formula(db: Session, input: "FormulaDeleteInput") -> FormulaDeletePayload:
  formula = get_formula(
    db=db,
    formula_slug=input.slug
  )

  if not formula:
    return FormulaDeletePayload(
      deleted_slug=None,
      deleted_name=None,
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Formula {input.slug} not found."
      )
    )

  db.delete(formula)
  db.commit()

  return FormulaDeletePayload(
    deleted_slug=input.slug,
    deleted_name=formula.name,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None
    )
  )
  
def update_formula(db: Session, identifier: "FormulaUpdateIdentifier", formula: "FormulaUpdateInput") -> FormulaUpdatePayload:
  formula_model = get_formula(
    db=db,
    formula_slug=identifier.slug
  )

  if not formula_model:
    return FormulaUpdatePayload(
      formula=None,
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Formula {identifier.slug} not found."
      )
    )

  if formula.slug:
    formula_model.slug = formula.slug

  if formula.name:
    formula_model.name = formula.name

  if formula.brand:
    formula_model.brand = formula.brand

  if formula.chill_type:
    formula_model.chill_type = models.ChillType[formula.chill_type.name]

  if formula.nic_type:
    formula_model.nic_type = models.NicType[formula.nic_type.name]

  db.commit()
  db.refresh(formula_model)
  return FormulaUpdatePayload(
    formula=FormulaType.from_model(formula_model),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None
    )
  )