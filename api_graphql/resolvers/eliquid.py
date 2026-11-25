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

from api_graphql.resolvers.flavor import get_or_create_flavor
from api_graphql.types.feedback import Feedback, FeedbackStatusEnum
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

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
  existing = db.scalar(select(Eliquid).where(Eliquid.sku == input.sku))
  
  if existing is not None:
    return EliquidCreatePayload(
      eliquid=EliquidType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"Eliquid with sku {input.sku} already exists",
      )
    )
  
  try:
    flavor = get_or_create_flavor(
      db,
      brand=input.brand,
      name=input.flavor_name,
      chill_type=ChillType[input.chill_type.name],
      nic_type=NicType[input.nic_type.name],
    )
  except SQLAlchemyError:
    return EliquidCreatePayload(
      eliquid=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Failed to get/create flavor {input.flavor_name}",
      )
    )
  
  formula_id = None
  feedback_message = None
  
  formula_identifier = input.formula
  if formula_identifier is not strawberry.UNSET:
    formula = db.scalar(select(Formula).where(formula_identifier.query_condition))
    if formula is None:
      feedback_message = f"Failed to connect Formula. Formula {formula_identifier.provided[1]} not found."
    elif formula.flavor_id != flavor.id:
      feedback_message = f"Failed to connect Formula. Formula {formula.slug} belongs to a different flavor."
    else:
      formula_id = formula.id
  
  eliquid = Eliquid(
    sku=input.sku,
    description=input.description,
    flavor_id=flavor.id,
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
      deleted_sku=None,
      deleted_description=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Eliquid {identifier.provided[1]} not found."
      )
    )
  
  sku = eliquid.sku
  description = eliquid.description
  
  db.delete(eliquid)
  db.commit()
  
  return EliquidDeletePayload(
    deleted_sku=sku,
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
  
  if formula.flavor_id != eliquid.flavor_id:
    return EliquidUpdatePayload(
      eliquid=EliquidType.from_model(eliquid),
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Formula {formula.slug} belongs to a different flavor than Eliquid {eliquid.description}."
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
  
  FLAVOR_FIELDS = ("brand", "flavor_name", "chill_type", "nic_type")
  flavor_changes = {
    attr: getattr(input, attr) for attr in FLAVOR_FIELDS
    if getattr(input, attr) is not strawberry.UNSET
  }
  
  if flavor_changes:
    current_flavor = eliquid.flavor
    new_brand = flavor_changes.get("brand", current_flavor.brand)
    new_name = flavor_changes.get("flavor_name", current_flavor.name)
    new_chill = ChillType[flavor_changes["chill_type"].name] if "chill_type" in flavor_changes else current_flavor.chill_type
    new_nic = NicType[flavor_changes["nic_type"].name] if "nic_type" in flavor_changes else current_flavor.nic_type
    
    new_flavor = get_or_create_flavor(db, brand=new_brand, name=new_name, chill_type=new_chill, nic_type=new_nic)
    
    if new_flavor.id != eliquid.flavor_id:
      if eliquid.formula is not None and eliquid.formula.flavor_id != new_flavor.id:
        eliquid.formula_id = None
        updated_columns.append("formula (cleared: different flavor)")
      eliquid.flavor = new_flavor
      db.flush()
      updated_columns.extend(a for a in flavor_changes)
  
  for attr, value in vars(input).items():
    if attr in FLAVOR_FIELDS or attr == "flavor_name":
      continue
    
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