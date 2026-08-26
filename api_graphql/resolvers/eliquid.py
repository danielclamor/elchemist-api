from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import select
import strawberry
from strawberry import relay

from api_graphql.types.eliquid import (
  EliquidType,
  EliquidCreatePayload,
  EliquidDeletePayload,
  EliquidUpdatePayload,
)
from api_graphql.types.enums import FeedbackStatus
from api_graphql.types.feedback import Feedback
from api_graphql.types.nic_profile import NicProfileType
import models

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from api_graphql.types.eliquid import (
    EliquidIdentifier,
    EliquidCreateInput,
    EliquidUpdateInput,
  )

# Queries
def get_all_eliquids(db: Session) -> list[models.Eliquid]:
  return (
    db.scalars(select(models.Eliquid)).all()
  )

def get_eliquid(db: Session, upc: str) -> models.Eliquid:
  return (
    db.scalar(select(models.Eliquid).where(models.Eliquid.upc == upc))
  )


# Mutations
def create_eliquid(db: Session, input: "EliquidCreateInput") -> EliquidCreatePayload:
  existing = db.scalar(select(models.Eliquid).where(models.Eliquid.upc == eliquid.upc))
  if existing:
    return EliquidCreatePayload(
      eliquid=EliquidType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatus.Cancelled,
        message=f"Eliquid with upc {input.upc} already exists",
      )
    )
  
  nic_profile_id = None
  
  nic_profile_slug = eliquid.nic_profile_slug
  if nic_profile_slug:
    nic_profile = db.scalar(select(models.NicProfile).where(models.NicProfile.slug == nic_profile_slug))
    if nic_profile:
      nic_profile_id = nic_profile.id
    else:
      connect_nic_profile_feedback = f"Failed to connect NicProfile. NicProfile {nic_profile_slug} not found."
  
  eliquid = models.Eliquid(
    upc=input.upc,
    description=input.description,
    brand=input.brand,
    chill_type=models.ChillType[input.chill_type.name],
    nic_type=models.NicType[input.nic_type.name],
    size=models.SizeOption[input.size.name],
    nic_level=models.NicLevelOption[input.nic_level.name],
    bottle_color=models.BottleColor[input.bottle_color.name],
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
  
def delete_eliquid(db: Session, identifier: "EliquidIdentifier") -> EliquidDeletePayload:
  eliquid = get_eliquid(db=db, upc=identifier.upc)
  
  if not eliquid:
    return EliquidDeletePayload(
      deleted_upc=None,
      deleted_description=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message="Eliquid not found."
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
  
def set_eliquid_nic_profile(db: Session, identifier: "EliquidIdentifier", nic_profile_id: relay.GlobalID | None) -> EliquidUpdatePayload:
  eliquid = get_eliquid(db=db, upc=identifier.upc)
  
  if not eliquid:
    return EliquidUpdatePayload(
      eliquid=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Eliquid {identifier} not found."
      )
    )
  
  if nic_profile_id:
    type_name = nic_profile_id.type_name
    node_id = nic_profile_id.node_id

    if type_name != NicProfileType.__strawberry_definition__.name:
      raise ValueError(f"Expected NicProfile GlobalId, got {type_name}")
    
    print(eliquid.nic_profile_id, node_id)
    if str(eliquid.nic_profile_id) == node_id:
      return EliquidUpdatePayload(
        eliquid=EliquidType.from_model(eliquid),
        feedback=Feedback(
          status=FeedbackStatus.CANCELLED,
          message="NicProfile already connected.",
        )
      )
    
    nic_profile = db.scalar(select(models.NicProfile).where(models.NicProfile.id == node_id))
    
    if not nic_profile:
      return EliquidUpdatePayload(
        eliquid=EliquidType.from_model(eliquid),
        feedback=Feedback(
          status=FeedbackStatus.FAILED,
          message="NicProfile not found."
        )
      )
      
    eliquid.nic_profile_id = nic_profile.id
  else:
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
  
def update_eliquid(db: Session, identifier: "EliquidIdentifier", input: "EliquidUpdateInput") -> EliquidUpdatePayload:
  eliquid = get_eliquid(db=db, upc=identifier.upc)
  
  if not eliquid:
    return EliquidUpdatePayload(
      eliquid=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Eliquid {identifier} not found."
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