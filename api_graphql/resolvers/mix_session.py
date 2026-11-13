from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import strawberry
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from typing import TYPE_CHECKING, Optional

from api_graphql.resolvers.utils import generate_session_number, get_today
from api_graphql.types.feedback import Feedback, FeedbackStatusEnum
from api_graphql.types.mix_session import MixSessionCreatePayload, MixSessionType, MixSessionUpdatePayload
from models import MixSession, MixSessionCounter, MixSessionStatus, Formula, ProductionOrder

if TYPE_CHECKING:
  from api_graphql.types.mix_session import MixSessionIdentifierInput
  from api_graphql.types.formula import FormulaIdentifierInput
  from api_graphql.types.production_order import ProductionOrderIdentifierInput

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
  production_order_identifiers: Optional[list["ProductionOrderIdentifierInput"]] = None,
) -> MixSessionCreatePayload:
  fetched_orders: list[ProductionOrder] = []

  if production_order_identifiers is not None:
    if not production_order_identifiers:
      return MixSessionCreatePayload(
        mix_session=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message="At least one production order must be provided when assigning orders.",
        ),
      )

    conditions = [ident.query_condition for ident in production_order_identifiers]
    
    fetched_orders = db.scalars(
      select(ProductionOrder)
      .options(joinedload(ProductionOrder.eliquid))
      .where(or_(*conditions))
    ).all()

    if len(fetched_orders) != len(production_order_identifiers):
      return MixSessionCreatePayload(
        mix_session=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message="One or more production orders could not be found.",
        ),
      )
    
    order_formula_ids = {po.eliquid.formula_id for po in fetched_orders}

    if None in order_formula_ids:
      return MixSessionCreatePayload(
        mix_session=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message="Cannot create MixSession: one or more orders have an unset formula.",
        ),
      )

    if len(order_formula_ids) > 1:
      return MixSessionCreatePayload(
        mix_session=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message="Cannot create MixSession: selected orders must have the same formula.",
        ),
      )
      
    orders_formula_id = fetched_orders[0].eliquid.formula_id
    
    assigned_session_ids = {
      po.mix_session_id
      for po in fetched_orders
      if po.mix_session_id is not None
    }
    has_unassigned = any(po.mix_session_id is None for po in fetched_orders)
    
    if len(assigned_session_ids) > 1:
      return MixSessionCreatePayload(
        mix_session=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message="Selected production orders belong to multiple different mix sessions.",
        ),
      )
    
    if len(assigned_session_ids) == 1:
      existing_session_id = assigned_session_ids.pop()
      existing_ms = db.scalar(
        select(MixSession).where(MixSession.id == existing_session_id)
      )

      if existing_ms is None:
        return MixSessionCreatePayload(
          mix_session=None,
          feedback=Feedback(
            status=FeedbackStatusEnum.FAILED,
            message="Existing MixSession referenced by orders was not found.",
          ),
        )

      # Rule 1: All orders are already in this exact mix session
      if not has_unassigned:
        return MixSessionCreatePayload(
          mix_session=MixSessionType.from_model(existing_ms),
          feedback=Feedback(
            status=FeedbackStatusEnum.CANCELLED,
            message=f"All selected production orders are already assigned to MixSession {existing_ms.session_number}.",
          ),
        )
        
      # Guard: Block adding remaining orders if the existing MixSession is no longer in progress
      if existing_ms.status != MixSessionStatus.IN_PROGRESS:
        return MixSessionCreatePayload(
          mix_session=None,
          feedback=Feedback(
            status=FeedbackStatusEnum.FAILED,
            message=f"Cannot assign remaining orders: MixSession {existing_ms.session_number} is {existing_ms.status.value}.",
          ),
        )

      # Rule 2: Some orders are in this mix session, and the rest are unassigned -> assign the rest
      try:
        for po in fetched_orders:
          if po.mix_session_id is None:
            po.mix_session_id = existing_ms.id

        db.commit()
        db.refresh(existing_ms)

        return MixSessionCreatePayload(
          mix_session=MixSessionType.from_model(existing_ms),
          feedback=Feedback(
            status=FeedbackStatusEnum.SUCCESS,
            message=f"Assigned remaining production orders to existing MixSession {existing_ms.session_number}.",
          ),
        )
      except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error assigning remaining orders to existing mix session")
        return MixSessionCreatePayload(
          mix_session=None,
          feedback=Feedback(
            status=FeedbackStatusEnum.FAILED,
            message="Could not assign remaining orders due to a database error.",
          ),
        )

  if formula is None and formula_identifier is not None:
    formula = db.scalar(
      select(Formula).where(formula_identifier.query_condition)
    )
    if formula is None:
      return MixSessionCreatePayload(
        mix_session=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message=f"Formula {formula_identifier.provided[1]} not found",
        ),
      )

  if fetched_orders:
    orders_formula_id = fetched_orders[0].eliquid.formula_id
    if formula is not None and formula.id != orders_formula_id:
      return MixSessionCreatePayload(
        mix_session=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message="Formula mismatch between provided formula and selected production orders.",
        ),
      )
    if formula is None:
      formula = db.scalar(
        select(Formula).where(Formula.id == orders_formula_id)
      )

  if formula is None:
    return MixSessionCreatePayload(
      mix_session=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Formula, formula identifier, or production orders must be provided.",
      ),
    )

  todate = get_today().date()

  try:
    db.execute(
      pg_insert(MixSessionCounter)
      .values(date=todate, last_number=0)
      .on_conflict_do_nothing()
    )
    counter = db.scalar(
      select(MixSessionCounter)
      .where(MixSessionCounter.date == todate)
      .with_for_update()
    )

    counter.last_number += 1
    db.flush()

    session_number = generate_session_number(
      day=todate, counter=counter.last_number
    )

    mix_session = MixSession(
      session_number=session_number,
      formula_id=formula.id,
      formula_name_snapshot=formula.name,
      status=MixSessionStatus.IN_PROGRESS,
    )

    db.add(mix_session)
    db.flush()

    for po in fetched_orders:
      po.mix_session_id = mix_session.id

    db.commit()
  except IntegrityError:
    db.rollback()
    logger.exception("Integrity error creating mix session")
    return MixSessionCreatePayload(
      mix_session=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Could not create MixSession: a database constraint was violated",
      ),
    )
  except SQLAlchemyError:
    db.rollback()
    logger.exception("Database error creating mix session")
    return MixSessionCreatePayload(
      mix_session=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Could not create MixSession due to a database error",
      ),
    )

  db.refresh(mix_session)

  return MixSessionCreatePayload(
    mix_session=MixSessionType.from_model(mix_session),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"MixSession {session_number} created",
    ),
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