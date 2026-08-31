from sqlalchemy.orm import Session
from sqlalchemy import select
import models

from api_graphql.resolvers.utils import generate_slug

from api_graphql.types.feedback import Feedback, FeedbackStatus

from api_graphql.types.flavoring_option import (
  FlavoringOptionType,
  FlavoringOptionCreatePayload,
  FlavoringOptionsBulkCreatePayload,
  FlavoringOptionDeletePayload,
  FlavoringOptionsBulkDeletePayload
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from api_graphql.types.flavoring_option import (
    FlavoringOptionIdentifierInput,
    FlavoringOptionCreateInput,
  )


# Queries
def get_all_flavoring_options(db: Session) -> list[models.FlavoringOption]:
  return (
    db.scalars(select(models.FlavoringOption)).all()
  )
  
def get_flavoring_option(db: Session, identifier: "FlavoringOptionIdentifierInput") -> models.FlavoringOption:
  return (
    db.scalar(select(models.FlavoringOption).where(identifier.query_condition))
  )
  

# Mutations
def create_flavoring_option(db: Session, input: "FlavoringOptionCreateInput") -> FlavoringOptionCreatePayload:
  slug = generate_slug(input.name)
  
  existing = db.scalar(select(models.FlavoringOption).where(models.FlavoringOption.slug == slug))
  
  if existing:
    return FlavoringOptionCreatePayload(
      flavoring_option=FlavoringOptionType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"FlavoringOption already exists",
      )
    )

  flavoring_option = models.FlavoringOption(
    slug=slug,
    name=input.name,
    is_vg=input.is_vg,
  )

  db.add(flavoring_option)
  db.commit()
  db.refresh(flavoring_option)
  
  return FlavoringOptionCreatePayload(
    flavoring_option=FlavoringOptionType.from_model(flavoring_option),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def bulk_create_flavoring_options(db: Session, inputs: list["FlavoringOptionCreateInput"]) -> FlavoringOptionsBulkCreatePayload:
  if len(inputs) == 0:
    return FlavoringOptionsBulkCreatePayload(
      flavoring_options=[],
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message="Nothing to add",
      )
    )
  
  flavoring_options = []
  
  for input in inputs:
    flavoring_options.append(create_flavoring_option(db=db, input=input))
  
  return FlavoringOptionsBulkCreatePayload(
    flavoring_options=flavoring_options,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def delete_flavoring_option(db: Session, identifier: "FlavoringOptionIdentifierInput") -> FlavoringOptionDeletePayload:
  flavoring_option = get_flavoring_option(db=db, identifier=identifier)
  
  if not flavoring_option:
    return FlavoringOptionDeletePayload(
      deleted_slug=None,
      deleted_name=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"FlavoringOption {identifier.provided} not found."
      )
    )
  
  db.delete(flavoring_option)
  db.commit()
  
  return FlavoringOptionDeletePayload(
    deleted_slug=flavoring_option.slug,
    deleted_name=flavoring_option.name,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def bulk_delete_flavoring_options(db: Session, identifiers: list["FlavoringOptionIdentifierInput"]) -> FlavoringOptionsBulkDeletePayload:  
  if len(identifiers) == 0:
    return FlavoringOptionsBulkDeletePayload(
      deleted=[],
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message="Nothing to delete",
      )
    )
  
  deleted = []
  
  for identifier in identifiers:
    deleted.append(delete_flavoring_option(db=db, identifier=identifier))
  
  return FlavoringOptionsBulkDeletePayload(
    deleted=deleted,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )