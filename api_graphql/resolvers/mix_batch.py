from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import strawberry
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from typing import TYPE_CHECKING, Optional

from api_graphql.resolvers.utils import generate_mix_number
from api_graphql.types.feedback import Feedback, FeedbackStatusEnum
from api_graphql.types.mix_batch import MixBatchCreatePayload, MixBatchType, MixBatchUpdatePayload
from models import MixBatch, MixBatchCounter, MixBatchStatus, NicProfile

if TYPE_CHECKING:
  from api_graphql.types.mix_batch import MixBatchIdentifierInput
  from api_graphql.types.nic_profile import NicProfileIdentifierInput

# Queries
def get_all_mix_batches(db: Session) -> list[MixBatch]:
  return db.scalars(select(MixBatch)).unique().all()

def get_mix_batch(db: Session, identifier: "MixBatchIdentifierInput") -> MixBatch:
  return db.scalar(select(MixBatch).where(identifier.query_condition))

# Mutations
def create_mix_batch(
  db: Session, 
  nic_profile_identifier: Optional["NicProfileIdentifierInput"] = None, 
  nic_profile: Optional["NicProfile"] = None,
) -> MixBatchCreatePayload:
  if nic_profile is None:
    if nic_profile_identifier is None:
      return MixBatchCreatePayload(
        mix_batch=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message=f"NicProfile or identifier must be provided"
        )
      )
      
    nic_profile = db.scalar(select(NicProfile).where(nic_profile_identifier.query_condition))
    if nic_profile is None:
      return MixBatchCreatePayload(
        mix_batch=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message=f"Nic Profile {nic_profile_identifier.provided[1]} not found"
        )
      )
  
  try:
    counter = db.scalar(
      select(MixBatchCounter).with_for_update()
    )
    
    if counter is None:
      count = db.execute(select(func.count(MixBatch.id))).scalar_one()
      counter = MixBatchCounter(last_number=count)
      db.add(counter)

    counter.last_number += 1
    db.flush()
    
    mix_number = generate_mix_number(counter=counter.last_number)
    
    mix_batch = MixBatch(
      mix_number=mix_number,
      nic_profile_id=nic_profile.id,
      nic_profile_full_name_snapshot=nic_profile.full_name,
      status=MixBatchStatus.IN_PROGRESS,
    )
    
    print(mix_batch)
    
    db.add(mix_batch)
    db.commit()
  except IntegrityError:
    db.rollback()
    logger.exception("Integrity error creating mix batch")
    return MixBatchCreatePayload(
      mix_batch=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Could not create MixBatch: a database constraint was violated",
      )
    )
  except SQLAlchemyError:
    db.rollback()
    logger.exception("Database error creating mix batch")
    return MixBatchCreatePayload(
      mix_batch=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Could not create MixBatch due to a database error",
      )
    )
    
  db.refresh(mix_batch)
  
  return MixBatchCreatePayload(
    mix_batch=MixBatchType.from_model(mix_batch),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"MixBatch {mix_number} created",
    )
  )
  
ALLOWED_MIX_BATCH_TRANSITIONS = {
  MixBatchStatus.IN_PROGRESS: {MixBatchStatus.MIXED, MixBatchStatus.CANCELLED},
  MixBatchStatus.MIXED: {MixBatchStatus.COMPLETED},
  MixBatchStatus.COMPLETED: set(),
  MixBatchStatus.CANCELLED: set(),
}

def change_mix_batch_status(batch: MixBatch, new_status: MixBatchStatus) -> None:
  if new_status not in ALLOWED_MIX_BATCH_TRANSITIONS[batch.status]:
    raise ValueError(f"Cannot change MixBatch from {batch.status.name} to {new_status.name}")
  
  batch.status = new_status
  
def mark_mix_batch_cancelled(db: Session, identifier: "MixBatchIdentifierInput") -> MixBatchUpdatePayload:
  batch = db.scalar(select(MixBatch).where(identifier.query_condition))
  
  if batch is None:
    return MixBatchUpdatePayload(
      mix_batch=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"MixBatch {identifier.provided[1]} not found",
      )
    )
    
  change_mix_batch_status(batch, MixBatchStatus.CANCELLED)
  
  db.commit()
  db.refresh()
  
  return MixBatchUpdatePayload(
    mix_batch=MixBatchType.from_model(batch),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )
  
def mark_mix_batch_completed(db: Session, identifier: "MixBatchIdentifierInput") -> MixBatchUpdatePayload:
  batch = db.scalar(select(MixBatch).where(identifier.query_condition))
  
  if batch is None:
    return MixBatchUpdatePayload(
      mix_batch=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"MixBatch {identifier.provided[1]} not found",
      )
    )
    
  change_mix_batch_status(batch, MixBatchStatus.COMPLETED)
  
  db.commit()
  db.refresh()
  
  return MixBatchUpdatePayload(
    mix_batch=MixBatchType.from_model(batch),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def mark_mix_batch_mixed(db: Session, identifier: "MixBatchIdentifierInput") -> MixBatchUpdatePayload:
  batch = db.scalar(select(MixBatch).where(identifier.query_condition))
  
  if batch is None:
    return MixBatchUpdatePayload(
      mix_batch=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"MixBatch {identifier.provided[1]} not found",
      )
    )
    
  change_mix_batch_status(batch, MixBatchStatus.MIXED)
  
  db.commit()
  db.refresh()
  
  return MixBatchUpdatePayload(
    mix_batch=MixBatchType.from_model(batch),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )