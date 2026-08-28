from sqlalchemy.orm import Session
from sqlalchemy import select
import models

from api_graphql.resolvers.utils import generate_slug

from api_graphql.types.feedback import Feedback, FeedbackStatus

from api_graphql.types.flavoring_option import (
  FlavoringOptionType,
  FlavoringOptionCreateInput, 
  FlavoringOptionCreatePayload
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from api_graphql.types.flavoring_option import FlavoringOptionIdentifierInput

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
def create_flavoring_option(db: Session, input: FlavoringOptionCreateInput) -> FlavoringOptionCreatePayload:
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
      status=FeedbackStatus.SUCESS,
      message=None,
    )
  )