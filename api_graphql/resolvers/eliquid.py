from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import select
import strawberry

from models import (
  Eliquid, 
  Formula, 
  ChillType, 
  NicType, 
  BottleSize, 
  NicLevel, 
  BottleColor
)

from api_graphql.types.eliquid import (
  EliquidType,
  EliquidCreatePayload,
  EliquidDeletePayload,
  EliquidUpdatePayload,
)

from api_graphql.types.feedback import Feedback, FeedbackStatusEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from api_graphql.types.eliquid import (
    EliquidIdentifierInput,
    EliquidCreateInput,
    EliquidUpdateInput,
  )
  
  from api_graphql.types.formula import FormulaIdentifierInput

# Queries
def get_all_eliquids(db: Session) -> list[Eliquid]:
  return (
    db.scalars(select(Eliquid)).all()
  )

def get_eliquid(db: Session, identifier: "EliquidIdentifierInput") -> Eliquid | None:
  return (
    db.scalar(select(Eliquid).where(identifier.query_condition))
  )


# Mutations
def create_eliquid(db: Session, input: "EliquidCreateInput") -> EliquidCreatePayload:
  existing = db.scalar(select(Eliquid).where(Eliquid.upc == input.upc))
  
  if existing is not None:
    return EliquidCreatePayload(
      eliquid=EliquidType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatusEnum.Cancelled,
        message=f"Eliquid with upc {input.upc} already exists",
      )
    )
  
  formula_id = None
  feedback_message = None
  
  formula_identifier = input.formula
  if formula_identifier is not strawberry.UNSET:
    formula = db.scalar(select(Formula).where(formula_identifier.query_condition))
    if formula is not None:
      formula_id = formula.id
    else:
      feedback_message = f"Failed to connect Formula. Formula {formula_identifier.provided[1]} not found."
  
  eliquid = Eliquid(
    upc=input.upc,
    description=input.description,
    brand=input.brand,
    chill_type=ChillType[input.chill_type.name],
    nic_type=NicType[input.nic_type.name],
    bottle_size=BottleSize[input.bottle_size.name],
    nic_level=NicLevel[input.nic_level.name],
    bottle_color=BottleColor[input.bottle_color.name],
    formula_id=formula_id,
  )
  
  db.add(eliquid)
  db.commit()
  db.refresh(eliquid)
  
  return EliquidCreatePayload(
    eliquid=EliquidType.from_model(eliquid),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=feedback_message,
    )
  )
  
def delete_eliquid(db: Session, identifier: "EliquidIdentifierInput") -> EliquidDeletePayload:
  eliquid = get_eliquid(db=db, identifier=identifier)
  
  if eliquid is None:
    return EliquidDeletePayload(
      deleted_upc=None,
      deleted_description=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Eliquid {identifier.provided[1]} not found."
      )
    )
  
  upc = eliquid.upc
  description = eliquid.description
  
  db.delete(eliquid)
  db.commit()
  
  return EliquidDeletePayload(
    deleted_upc=upc,
    deleted_description=description,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None
    )
  )
  
def set_eliquid_formula(db: Session, identifier: "EliquidIdentifierInput", formula_identifier: "FormulaIdentifierInput") -> EliquidUpdatePayload:
  eliquid = get_eliquid(db=db, identifier=identifier)
  
  if eliquid is None:
    return EliquidUpdatePayload(
      eliquid=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Eliquid {identifier.provided[1]} not found."
      )
    )

  formula = db.scalar(select(Formula).where(formula_identifier.query_condition))
  
  if formula is None:
    return EliquidUpdatePayload(
      eliquid=EliquidType.from_model(eliquid),
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Formula {formula_identifier.provided[1]} not found."
      )
    )
  
  if eliquid.formula_id == formula.id:
    return EliquidUpdatePayload(
      eliquid=EliquidType.from_model(eliquid),
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"Eliquid {eliquid.description} already connected to Formula {formula.slug}."
      )
    )
    
  eliquid.formula_id = formula.id
  
  db.commit()
  db.refresh(eliquid)
  
  return EliquidUpdatePayload(
    eliquid=EliquidType.from_model(eliquid),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def unset_eliquid_formula(db: Session, identifier: "EliquidIdentifierInput") -> EliquidUpdatePayload:
  eliquid = get_eliquid(db=db, identifier=identifier)
  
  if eliquid is None:
    return EliquidUpdatePayload(
      eliquid=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Eliquid {identifier.provided[1]} not found."
      )
    )
  
  if eliquid.formula_id is None:
    return EliquidUpdatePayload(
      eliquid=EliquidType.from_model(eliquid),
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"Eliquid {eliquid.description} is not connected to any Formula."
      )
    )
  
  eliquid.formula_id = None
  
  db.commit()
  db.refresh(eliquid)
  
  return EliquidUpdatePayload(
    eliquid=EliquidType.from_model(eliquid),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )
  
def update_eliquid(db: Session, identifier: "EliquidIdentifierInput", input: "EliquidUpdateInput") -> EliquidUpdatePayload:
  eliquid = get_eliquid(db=db, identifier=identifier)

  if eliquid is None:
    return EliquidUpdatePayload(
      eliquid=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Eliquid {identifier.provided[1]} not found."
      )
    )
  
  updated_columns = []
  
  for attr, value in vars(input).items():
    current = getattr(eliquid, attr, None)
    
    if value is strawberry.UNSET:
      continue
    if isinstance(value, Enum):
      value = value.name
      current = current.name if current else None
    
    if value != current:
      setattr(eliquid, attr, value)
      db.flush()
      updated_columns.append(attr)
  
  if len(updated_columns) == 0:
    message = "Nothing to update"
  else:
    db.commit()
    db.refresh(eliquid)
    
    message = f"Updated {', '.join(updated_columns)}"
    
  return EliquidUpdatePayload(
    eliquid=EliquidType.from_model(eliquid),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=message
    )
  )