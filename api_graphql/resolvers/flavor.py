from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import strawberry

from .utils import generate_slug

from models import Flavor, ChillType, NicType

from api_graphql.types.feedback import Feedback, FeedbackStatusEnum

from api_graphql.types.flavor import (
  FlavorType, 
  FlavorCreatePayload, 
  FlavorDeletePayload, 
  FlavorUpdatePayload
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from api_graphql.types.flavor import (
    FlavorIdentifierInput,
    FlavorCreateInput,
    FlavorUpdateInput,
  )

# Queries
def get_all_flavors(db: Session) -> list[Flavor]:
  return (
    db.scalars(select(Flavor))
    .unique()
    .all()
  )
  
def get_flavor(db: Session, identifier: "FlavorIdentifierInput") -> Flavor | None:
  return (
    db.scalar(select(Flavor).where(identifier.query_condition))
  )


# Mutations
def create_flavor(db: Session, input: "FlavorCreateInput") -> FlavorCreatePayload:
  slug = generate_slug(string=input.name)

  existing = db.scalar(select(Flavor).where(Flavor.slug == slug))
  
  if existing is not None:
    return FlavorCreatePayload(
      flavor=FlavorType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"Flavor {slug} already exists",
      )
    )

  flavor = Flavor(
    slug=slug,
    name=input.name,
    brand=input.brand,
    chill_type=ChillType[input.chill_type.name],
    nic_type=NicType[input.nic_type.name],
  )

  db.add(flavor)
  db.commit()
  db.refresh(flavor)
  
  return FlavorCreatePayload(
    flavor=FlavorType.from_model(flavor),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def delete_flavor(db: Session, identifier: "FlavorIdentifierInput") -> FlavorDeletePayload:
  flavor = get_flavor(db=db, identifier=identifier)
  
  if flavor is None:
    return FlavorDeletePayload(
      deleted_slug=None,
      deleted_name=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Flavor {identifier.provided} not found."
      )
    )
  
  slug = flavor.slug
  name = flavor.name

  db.delete(flavor)
  db.commit()

  return FlavorDeletePayload(
    deleted_slug=slug,
    deleted_name=name,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )
  
def update_flavor(db: Session, identifier: "FlavorIdentifierInput", input: "FlavorUpdateInput") -> FlavorUpdatePayload:
  flavor = get_flavor(db=db, identifier=identifier)
  
  if flavor is None:
    return FlavorUpdatePayload(
      flavor=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Flavor not found."
      )
    )
  
  updated_columns = []
  
  for attr, value in vars(input).items():
    current = getattr(flavor, attr, None)
    
    if value is strawberry.UNSET:
      continue
    
    if isinstance(value, Enum):
      value = value.name
      current = current.name if current else None
      
    if value != current:
      setattr(flavor, attr, value)
      db.flush()
      updated_columns.append(attr)
      
  if len(updated_columns) == 0:
    message = "Nothing to update"
  else:
    db.commit()
    db.refresh(flavor)
    message = f"Updated {', '.join(updated_columns)}"

  db.commit()
  db.refresh(flavor)
  
  return FlavorUpdatePayload(
    flavor=FlavorType.from_model(flavor),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=message
    )
  )