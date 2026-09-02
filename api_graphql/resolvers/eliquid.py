from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import select
import strawberry

from models import (
  Eliquid, 
  NicProfile, 
  ChillType, 
  NicType, 
  SizeOption, 
  NicLevelOption, 
  BottleColor
)

from api_graphql.types.eliquid import (
  EliquidType,
  EliquidCreatePayload,
  EliquidDeletePayload,
  EliquidUpdatePayload,
)

from api_graphql.types.feedback import Feedback, FeedbackStatus

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from api_graphql.types.eliquid import (
    EliquidIdentifierInput,
    EliquidCreateInput,
    EliquidUpdateInput,
  )
  
  from api_graphql.types.nic_profile import NicProfileIdentifierInput

# Queries
def get_all_eliquids(db: Session) -> list[Eliquid]:
  return (
    db.scalars(select(Eliquid)).all()
  )

def get_eliquid(db: Session, identifier: "EliquidIdentifierInput") -> Eliquid:
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
        status=FeedbackStatus.Cancelled,
        message=f"Eliquid with upc {input.upc} already exists",
      )
    )
  
  nic_profile_id = None
  
  nic_profile_identifier = input.nic_profile
  if nic_profile_identifier is not strawberry.UNSET:
    nic_profile = db.scalar(select(NicProfile).where(nic_profile_identifier.query_condition))
    if nic_profile is not None:
      nic_profile_id = nic_profile.id
    else:
      connect_nic_profile_feedback = f"Failed to connect NicProfile. NicProfile {nic_profile_identifier.provided[1]} not found."
  
  eliquid = Eliquid(
    upc=input.upc,
    description=input.description,
    brand=input.brand,
    chill_type=ChillType[input.chill_type.name],
    nic_type=NicType[input.nic_type.name],
    size=SizeOption[input.size.name],
    nic_level=NicLevelOption[input.nic_level.name],
    bottle_color=BottleColor[input.bottle_color.name],
    nic_profile_id=nic_profile_id,
  )
  
  db.add(eliquid)
  db.commit()
  db.refresh(eliquid)
  
  return EliquidCreatePayload(
    eliquid=EliquidType.from_model(eliquid),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=connect_nic_profile_feedback or None
    )
  )
  
def delete_eliquid(db: Session, identifier: "EliquidIdentifierInput") -> EliquidDeletePayload:
  eliquid = get_eliquid(db=db, identifier=identifier)
  
  if eliquid is None:
    return EliquidDeletePayload(
      deleted_upc=None,
      deleted_description=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Eliquid {identifier.provided[1]} not found."
      )
    )
  
  db.delete(eliquid)
  db.commit()
  
  return EliquidDeletePayload(
    deleted_upc=eliquid.upc,
    deleted_description=eliquid.description,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None
    )
  )
  
def set_eliquid_nic_profile(db: Session, identifier: "EliquidIdentifierInput", nic_profile_identifier: "NicProfileIdentifierInput") -> EliquidUpdatePayload:
  eliquid = get_eliquid(db=db, identifier=identifier)
  
  if eliquid is None:
    return EliquidUpdatePayload(
      eliquid=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Eliquid {identifier.provided[1]} not found."
      )
    )

  nic_profile = db.scalar(select(NicProfile).where(nic_profile_identifier.query_condition))
  
  if nic_profile is None:
    return EliquidUpdatePayload(
      eliquid=EliquidType.from_model(eliquid),
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"NicProfile {nic_profile_identifier.provided[1]} not found."
      )
    )
  
  if eliquid.nic_profile_id == nic_profile.id:
    return EliquidUpdatePayload(
      eliquid=EliquidType.from_model(eliquid),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Eliquid {eliquid.description} already connected to NicProfile {nic_profile.slug}."
      )
    )
    
  eliquid.nic_profile_id = nic_profile.id
  
  db.commit()
  db.refresh(eliquid)
  
  return EliquidUpdatePayload(
    eliquid=EliquidType.from_model(eliquid),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def unset_eliquid_nic_profile(db: Session, identifier: "EliquidIdentifierInput") -> EliquidUpdatePayload:
  eliquid = get_eliquid(db=db, identifier=identifier)
  
  if eliquid is None:
    return EliquidUpdatePayload(
      eliquid=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Eliquid {identifier.provided[1]} not found."
      )
    )
  
  if eliquid.nic_profile_id is None:
    return EliquidUpdatePayload(
      eliquid=EliquidType.from_model(eliquid),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Eliquid {eliquid.description} is not connected to any NicProfile."
      )
    )
  
  eliquid.nic_profile_id = None
  
  db.commit()
  db.refresh(eliquid)
  
  return EliquidUpdatePayload(
    eliquid=EliquidType.from_model(eliquid),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )
  
def update_eliquid(db: Session, identifier: "EliquidIdentifierInput", input: "EliquidUpdateInput") -> EliquidUpdatePayload:
  eliquid = get_eliquid(db=db, identifier=identifier)

  if eliquid is None:
    return EliquidUpdatePayload(
      eliquid=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
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
      current = current.name
    
    if value != current:
      setattr(eliquid, attr, value)
      db.flush()
      updated_columns.append(f"{attr}")
  
  if len(updated_columns) == 0:
    message = "Nothing to update"
  else:
    db.commit()
    db.refresh(eliquid)
    
    message = f"Updated {", ".join(updated_columns)}"
    
  return EliquidUpdatePayload(
    eliquid=EliquidType.from_model(eliquid),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=message
    )
  )