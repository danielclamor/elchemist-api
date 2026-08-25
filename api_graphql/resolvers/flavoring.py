from sqlalchemy.orm import Session
from sqlalchemy import select
import models

from api_graphql.resolvers.utils import generate_slug

from api_graphql.types.flavoring import FlavoringOptionCreateInput

# Queries
def get_all_flavoring_options(db: Session) -> list[models.FlavoringOption]:
  return (
    db.scalars(select(models.FlavoringOption)).all()
  )
  
def get_flavoring_option(db: Session, flavoring_option_slug: str) -> models.FlavoringOption:
  return (
    db.scalar(select(models.FlavoringOption).where(models.FlavoringOption.slug == flavoring_option_slug))
  )
  
  
# Mutations
def create_flavoring_option(db: Session, flavoring_option: FlavoringOptionCreateInput) -> models.FlavoringOption:
  flavoring_option_slug = generate_slug(flavoring_option.name)

  flavoring_option = models.FlavoringOption(
    slug=flavoring_option_slug,
    name=flavoring_option.name,
    is_vg=flavoring_option.is_vg,
  )

  db.add(flavoring_option)
  db.commit()
  db.refresh(flavoring_option)
  return flavoring_option