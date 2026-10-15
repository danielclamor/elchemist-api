from sqlalchemy.orm import Session
from sqlalchemy import select

from models import Location

from api_graphql.types.feedback import Feedback, FeedbackStatusEnum
from api_graphql.types.location import LocationType, LocationUpdatePayload

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from api_graphql.types.location import (
    LocationIdentifierInput
  )

def get_all_locations(db: Session, include_archived: bool = False) -> list[Location]:
  stmt = select(Location).order_by(Location.name.asc())

  if not include_archived:
    stmt = stmt.where(Location.is_archived.is_(False))

  return db.scalars(stmt).unique().all()
  
def get_location(db: Session, identifier: "LocationIdentifierInput") -> Location | None:
  return (
    db.scalar(select(Location).where(identifier.query_condition))
  )
  
def get_hq_location(db: Session) -> Location | None:
  return (
    db.scalar(select(Location).where(Location.is_hq.is_(True)))
  )


def set_location_archived(db: Session, identifier: "LocationIdentifierInput", is_archived: bool) -> LocationUpdatePayload:
  location = get_location(db=db, identifier=identifier)

  if location is None:
    return LocationUpdatePayload(
      location=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Location {identifier.provided[1]} not found"
      )
    )

  if is_archived and location.is_hq:
    return LocationUpdatePayload(
      location=LocationType.from_model(location),
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Location {location.code} is HQ. Mark another location as HQ before archiving it"
      )
    )

  if location.is_archived == is_archived:
    return LocationUpdatePayload(
      location=LocationType.from_model(location),
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"Location {location.code} is already {'archived' if is_archived else 'active'}"
      )
    )

  location.is_archived = is_archived
  db.commit()
  db.refresh(location)

  return LocationUpdatePayload(
    location=LocationType.from_model(location),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"Location {location.code} {'archived' if is_archived else 'restored'}"
    )
  )
