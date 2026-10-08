from sqlalchemy.orm import Session
from sqlalchemy import select

from models import Location

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from api_graphql.types.location import (
    LocationIdentifierInput
  )

def get_all_locations(db: Session) -> list[Location]:
  return (
    db.scalars(select(Location))
    .unique()
    .all()
  )
  
def get_location(db: Session, identifier: "LocationIdentifierInput") -> Location | None:
  return (
    db.scalar(select(Location).where(identifier.query_condition))
  )
  
def get_hq_location(db: Session) -> Location | None:
  return (
    db.scalar(select(Location).where(Location.is_hq.is_(True)))
  )