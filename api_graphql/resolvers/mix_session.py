from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import strawberry
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from typing import TYPE_CHECKING, Optional

from api_graphql.resolvers.utils import generate_session_number, get_today
from api_graphql.types.feedback import Feedback, FeedbackStatusEnum
from api_graphql.types.mix_session import MixSessionCreatePayload, MixSessionType, MixSessionUpdatePayload
from models import MixSession, MixSessionCounter, MixSessionStatus, Formula

if TYPE_CHECKING:
  from api_graphql.types.mix_session import MixSessionIdentifierInput
  from api_graphql.types.formula import FormulaIdentifierInput

# Queries
def get_all_mix_sessions(db: Session) -> list[MixSession]:
  return db.scalars(select(MixSession)).unique().all()

def get_mix_session(db: Session, identifier: "MixSessionIdentifierInput") -> MixSession:
  return db.scalar(select(MixSession).where(identifier.query_condition))

# Mutations
def create_mix_session(
  db: Session, 
  formula_identifier: Optional["FormulaIdentifierInput"] = None, 
  formula: Optional["Formula"] = None,
) -> MixSessionCreatePayload:
  if formula is None:
    if formula_identifier is None:
      return MixSessionCreatePayload(
        mix_session=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message=f"Formula or identifier must be provided"
        )
      )
      
    formula = db.scalar(select(Formula).where(formula_identifier.query_condition))
    if formula is None:
      return MixSessionCreatePayload(
        mix_session=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message=f"Nic Profile {formula_identifier.provided[1]} not found"
        )
      )
  
  todate = get_today().date()
  
  try:
    # make sure today's counter row exists (a second request waits instead of failing
    # on a duplicate insert), then lock it while the number is handed out
    db.execute(pg_insert(MixSessionCounter).values(date=todate, last_number=0).on_conflict_do_nothing())
    counter = db.scalar(
      select(MixSessionCounter).where(MixSessionCounter.date == todate).with_for_update()
    )

    counter.last_number += 1
    db.flush()
    
    session_number = generate_session_number(day=todate, counter=counter.last_number)
    
    mix_session = MixSession(
      session_number=session_number,
      formula_id=formula.id,
      formula_name_snapshot=formula.name,
      status=MixSessionStatus.IN_PROGRESS,
    )
    
    print(mix_session)
    
    db.add(mix_session)
    db.commit()
  except IntegrityError:
    db.rollback()
    logger.exception("Integrity error creating mix session")
    return MixSessionCreatePayload(
      mix_session=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Could not create MixSession: a database constraint was violated",
      )
    )
  except SQLAlchemyError:
    db.rollback()
    logger.exception("Database error creating mix session")
    return MixSessionCreatePayload(
      mix_session=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Could not create MixSession due to a database error",
      )
    )
    
  db.refresh(mix_session)
  
  return MixSessionCreatePayload(
    mix_session=MixSessionType.from_model(mix_session),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"MixSession {session_number} created",
    )
  )
  
ALLOWED_MIX_SESSION_TRANSITIONS = {
  MixSessionStatus.IN_PROGRESS: {MixSessionStatus.MIXED, MixSessionStatus.CANCELLED},
  MixSessionStatus.MIXED: {MixSessionStatus.COMPLETED},
  MixSessionStatus.COMPLETED: set(),
  MixSessionStatus.CANCELLED: set(),
}

def change_mix_session_status(batch: MixSession, new_status: MixSessionStatus) -> None:
  if new_status not in ALLOWED_MIX_SESSION_TRANSITIONS[batch.status]:
    raise ValueError(f"Cannot change MixSession from {batch.status.name} to {new_status.name}")
  
  batch.status = new_status
  
def mark_mix_session_cancelled(db: Session, identifier: "MixSessionIdentifierInput") -> MixSessionUpdatePayload:
  batch = db.scalar(select(MixSession).where(identifier.query_condition))
  
  if batch is None:
    return MixSessionUpdatePayload(
      mix_session=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"MixSession {identifier.provided[1]} not found",
      )
    )
    
  change_mix_session_status(batch, MixSessionStatus.CANCELLED)
  
  db.commit()
  db.refresh()
  
  return MixSessionUpdatePayload(
    mix_session=MixSessionType.from_model(batch),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )
  
def mark_mix_session_completed(db: Session, identifier: "MixSessionIdentifierInput") -> MixSessionUpdatePayload:
  batch = db.scalar(select(MixSession).where(identifier.query_condition))
  
  if batch is None:
    return MixSessionUpdatePayload(
      mix_session=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"MixSession {identifier.provided[1]} not found",
      )
    )
    
  change_mix_session_status(batch, MixSessionStatus.COMPLETED)
  
  db.commit()
  db.refresh()
  
  return MixSessionUpdatePayload(
    mix_session=MixSessionType.from_model(batch),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def mark_mix_session_mixed(db: Session, identifier: "MixSessionIdentifierInput") -> MixSessionUpdatePayload:
  batch = db.scalar(select(MixSession).where(identifier.query_condition))
  
  if batch is None:
    return MixSessionUpdatePayload(
      mix_session=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"MixSession {identifier.provided[1]} not found",
      )
    )
    
  change_mix_session_status(batch, MixSessionStatus.MIXED)
  
  db.commit()
  db.refresh()
  
  return MixSessionUpdatePayload(
    mix_session=MixSessionType.from_model(batch),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )