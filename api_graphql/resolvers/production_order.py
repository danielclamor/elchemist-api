from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from datetime import datetime
from enum import Enum
import uuid

from graphql import GraphQLError
import strawberry

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from zoneinfo import ZoneInfo

from api_graphql.resolvers.location import get_hq_location
from models import (
  Eliquid,
  Location,
  ProductionOrder,
  ProductionOrderAllocation,
  ProductionOrderJobType,
  MixJob,
  MixJobStatus,
  # RepatJob,
  # RepatJobStatus,
  ProductionOrderStatus,
  ProductionOrderActivityLog,
  ProductionOrderActivityType,
  ProductionOrderCounter,
)

from api_graphql.types.feedback import Feedback, FeedbackStatusEnum

from api_graphql.types.eliquid import EliquidIdentifierInput

from api_graphql.types.production_order import (
  ProductionOrderIdentifierInput,
  ProductionOrderAssignJobPayload,
  ProductionOrderJobCreatePayload,
  MixJobType,
  MixJobIdentifierInput,
  MixJobUpdatePayload,
  # RepatJobType,
  # RepatJobIdentifierInput,
  # RepatJobUpdatePayload,
  ProductionOrderType,
  ProductionOrderCreatePayload,
  ProductionOrderDeletePayload,
  ProductionOrderUpdatePayload,
)

from api_graphql.types.enums import ProductionOrderJobTypeEnum

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
  from api_graphql.types.production_order import (
    MixJobMarkMixedInput,
    # RepatJobMarkCompletedInput,
    ProductionOrderCreateInput,
    ProductionOrderUpdateInput,
  )

from .utils import generate_job_number, generate_production_order_number, get_today, convert_strawberry_input_to_dict

# Queries
def _filter_production_orders(stmt, job_type: "ProductionOrderJobType"=None, status:"ProductionOrderStatus"=None, created_from:datetime=None, created_to:datetime=None):
  if job_type is not None:
    stmt = stmt.where(ProductionOrder.job_type == job_type)
  if status is not None:
    stmt = stmt.where(ProductionOrder.status == status)
  if created_from is not None:
    stmt = stmt.where(ProductionOrder.created_at >= created_from)
  if created_to is not None:
    stmt = stmt.where(ProductionOrder.created_at < created_to)
  return stmt

def get_all_production_orders(db: Session, job_type: "ProductionOrderJobType"=None, status:"ProductionOrderStatus"=None, created_from:datetime=None, created_to:datetime=None) -> list[ProductionOrder]:
  stmt = (
    select(ProductionOrder)
    .options(
      selectinload(ProductionOrder.activity_logs),
      selectinload(ProductionOrder.allocations).selectinload(ProductionOrderAllocation.location),
      selectinload(ProductionOrder.hq_location),
      selectinload(ProductionOrder.mix_jobs),
      # selectinload(ProductionOrder.repat_jobs),
    )
    .order_by(ProductionOrder.created_at.desc(), ProductionOrder.id)
  )
  stmt = _filter_production_orders(stmt, job_type, status, created_from, created_to)
  return db.scalars(stmt).unique().all()

def get_production_order_status_counts(db: Session, created_from=None, created_to=None) -> dict:
  stmt = select(ProductionOrder.status, func.count()).group_by(ProductionOrder.status)
  stmt = _filter_production_orders(stmt, None, created_from, created_to)
  return {status: count for status, count in db.execute(stmt).all()}

def get_all_mix_jobs(db: Session) -> list[MixJob]:
  return (
    db.scalars(select(MixJob)).unique().all()
  )
  
# def get_all_repat_jobs(db: Session) -> list[RepatJob]:
#   return (
#     db.scalars(select(RepatJob)).unique().all()
#   )

def get_production_order(db: Session, identifier: "ProductionOrderIdentifierInput") -> ProductionOrder | None:
  return (
    db.scalar(select(ProductionOrder).where(identifier.query_condition))
  )
  
def get_mix_job(db: Session, identifier: "MixJobIdentifierInput") -> MixJob | None:
  return (
    db.scalar(select(MixJob).where(identifier.query_condition))
  )

# def get_repat_job(db: Session, identifier: "RepatJobIdentifierInput") -> RepatJob | None:
#   return (
#     db.scalar(select(RepatJob).where(identifier.query_condition))
#   )

# Mutations
def assign_production_order_job(db: Session, identifier: "ProductionOrderIdentifierInput", ordered_quantity: Optional[int], job_type: "ProductionOrderJobTypeEnum") -> ProductionOrderAssignJobPayload: 
  po = db.scalar(select(ProductionOrder).where(identifier.query_condition).with_for_update())

  if po is None:
    return ProductionOrderAssignJobPayload(
      production_order=None,
      created_production_order_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} not found"
      )
    )
  
  if po.status != ProductionOrderStatus.PENDING and po.status != ProductionOrderStatus.IN_PROGRESS:
    return ProductionOrderAssignJobPayload(
      production_order=ProductionOrderType.from_model(po),
      created_production_order_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Cannot assign ProductionOrder {identifier.provided[1]} in {po.status.name} status to a new job"
      )
    )
    
  old_job = po.job_type
  
  try:
    new_job = ProductionOrderJobType[job_type.name]
  except KeyError:
    return ProductionOrderAssignJobPayload(
      production_order=ProductionOrderType.from_model(po),
      created_production_order_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Job type {job_type.name} not supported",
      ),
    )
  
  if old_job == new_job:
    return ProductionOrderAssignJobPayload(
      production_order=ProductionOrderType.from_model(po),
      created_production_order_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"ProductionOrder {identifier.provided[1]} is already assigned to {job_type.name}"
      )
    )

  if new_job == ProductionOrderJobType.MIX and ordered_quantity is None:
    return ProductionOrderAssignJobPayload(
      production_order=ProductionOrderType.from_model(po),
      created_production_order_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Mix job needs an ordered quantity. Provide one, or set it on the production order",
      ),
    )
  
  # don't require orderedQuantity for other jobs than mix
  # if effective_quantity is not None and effective_quantity <= 0:
  #   return ProductionOrderAssignJobPayload(
  #     production_order=ProductionOrderType.from_model(po),
  #     created_production_order_job=None,
  #     feedback=Feedback(
  #       status=FeedbackStatusEnum.FAILED,
  #       message=f"Quantity must be greater than 0. Currently, {effective_quantity}",
  #     ),
  #   )
  
  if ordered_quantity is not strawberry.UNSET:
    set_qty_feedback = set_production_order_ordered_quantity(
      db, 
      ProductionOrderIdentifierInput(order_number=po.order_number), 
      ordered_quantity=ordered_quantity,
    ).feedback
    
    if set_qty_feedback.status == FeedbackStatusEnum.FAILED:
      return ProductionOrderAssignJobPayload(
        production_order=ProductionOrderType.from_model(po),
        created_production_order_job=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message=f"Failed setting ordered quantity. {set_qty_feedback.message}",
        ),
      )
  
  today_as_utc = get_today("UTC")
  
  current_job = po.current_job
  
  if old_job == ProductionOrderJobType.MIX and current_job is not None:
    reassigned_job = mark_mix_job_reassigned(
      db=db,
      identifier=MixJobIdentifierInput(job_number=current_job.job_number),
    ).mix_job
  # elif old_job == ProductionOrderJobType.REPAT:
  #   reassigned_job = mark_repat_job_reassigned(
  #     db=db,
  #     identifier=RepatJobIdentifierInput(job_number=current_job.job_number),
  #   ).repat_job
  else:
    reassigned_job = None
    
  if old_job is not None and reassigned_job is None:
    db.rollback()
    return ProductionOrderAssignJobPayload(
      production_order=ProductionOrderType.from_model(po),
      created_production_order_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Failed to reassign ProductionOrder {identifier.provided[1]} old {old_job} job"
      )
    )
   
  if new_job == ProductionOrderJobType.MIX:
    created_job = create_mix_job(
      db=db,
      production_order=po,
      created_at=today_as_utc,
      ordered_quantity=ordered_quantity,
    ).production_order_job
  # else:
  #   created_job = create_repat_job(
  #     db=db,
  #     production_order=po,
  #     created_at=today_as_utc,
  #     ordered_quantity=ordered_quantity,
  #   ).production_order_job
    
  po.job_type = new_job
  db.flush()
  
  create_production_order_activity_log(
    db=db, 
    production_order_id=po.id,
    type=ProductionOrderActivityType.ASSIGN_JOB,
    triggered_at=today_as_utc,
    old_value=f"{old_job.name if old_job is not None else None}",
    new_value=f"{new_job.name}"
  )

  mark_production_order_in_progress(db=db, identifier=ProductionOrderIdentifierInput(order_number=po.order_number))
  
  db.commit()
  db.refresh(po)
  
  return ProductionOrderAssignJobPayload(
    production_order=ProductionOrderType.from_model(po),
    created_production_order_job=created_job,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"Assigned to {new_job.name}"
    )
  )

def create_production_order(db: Session, eliquid_identifier: "EliquidIdentifierInput", input: "ProductionOrderCreateInput") -> ProductionOrderCreatePayload: 
  eliquid = db.scalar(select(Eliquid).where(eliquid_identifier.query_condition))
  
  if eliquid is None:
    return ProductionOrderCreatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Eliquid {eliquid_identifier.provided[1]} not found"
      )
    )
    
  hq = get_hq_location(db)

  if hq is None:
    return ProductionOrderCreatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="No HQ location is set. Mark one location as HQ first",
      ),
    )
    
  quantity = None if input.quantity in (None, strawberry.UNSET) else input.quantity
  allocation_inputs = [] if input.allocations in (None, strawberry.UNSET) else input.allocations
  
  resolved: list[tuple[Location, int]] = []
  
  if allocation_inputs:
    if quantity is None:
      return ProductionOrderCreatePayload(
        production_order=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message="Set an ordered quantity before allocating"
        )
      )
  
    seen: set[uuid.UUID] = set()
    
    for a in allocation_inputs:
      location = db.scalar(select(Location).where(a.location_identifier.query_condition))

      if location is None:
        return ProductionOrderCreatePayload(
          production_order=None,
          feedback=Feedback(
            status=FeedbackStatusEnum.FAILED,
            message=f"Location {a.location_identifier.provided[1]} not found"
          )
        )
      if location.is_archived:
        return ProductionOrderCreatePayload(
          production_order=None,
          feedback=Feedback(
            status=FeedbackStatusEnum.FAILED,
            message=f"Location {location.code} is archived. Restore it or allocate to another location"
          )
        )
      if location.is_hq:
        return ProductionOrderCreatePayload(
          production_order=None,
          feedback=Feedback(
            status=FeedbackStatusEnum.FAILED,
            message=f"Location {location.code} is HQ. HQ gets the remainder, allocate only to remote locations"
          )
        )
      if location.id in seen:
        return ProductionOrderCreatePayload(
          production_order=None,
          feedback=Feedback(
            status=FeedbackStatusEnum.FAILED,
            message=f"Duplicate allocation for location {location.code}"
          )
        )
      
      seen.add(location.id)
      resolved.append((location, a.quantity))
      
    allocated = sum(q for _, q in resolved)
    if allocated > quantity:
      return ProductionOrderCreatePayload(
        production_order=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message=f"Allocations ({allocated}) exceed ordered quantity ({quantity})"
        )
      )
        
  job_type = None if input.job_type in (None, strawberry.UNSET) else input.job_type
  
  if job_type == ProductionOrderJobTypeEnum.MIX and quantity is None:
    return ProductionOrderCreatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Set an ordered quantity before assigning to mix job"
      )
    )

  today = get_today()
  todate = today.date()
  created_at_utc = today.astimezone(ZoneInfo("UTC"))
  
  try: 
    counter = db.scalar(
      select(ProductionOrderCounter)
      .where(ProductionOrderCounter.date == todate)
      .with_for_update()
    )

    if counter is not None:
      counter.last_number += 1
    else:
      counter = ProductionOrderCounter(
        date=todate,
        last_number=1,
      )
      db.add(counter)

    db.flush()
    
    po_number = generate_production_order_number(date=todate, counter=counter.last_number)
    
    po = ProductionOrder(
      order_number=po_number,
      eliquid_id=eliquid.id,
      ordered_quantity=quantity,
      is_priority=input.is_priority,
      status=ProductionOrderStatus.PENDING,
      hq_location_id=hq.id,
      created_at=created_at_utc,
      updated_at=created_at_utc,
    )
    
    db.add(po)
    db.flush()
    
    for location, qty in resolved:
      create_production_order_allocation(
        db=db,
        production_order_id=po.id,
        location_id=location.id,
        quantity=qty,
      )
    
    create_production_order_activity_log(
      db=db,
      production_order_id=po.id,
      type=ProductionOrderActivityType.CREATED,
      triggered_at=created_at_utc,
      old_value=None,
      new_value=None,
    )
    
    db.commit()
    
    if job_type is not None:
      assign_production_order_job(
        db, 
        ProductionOrderIdentifierInput(order_number=po.order_number), 
        ordered_quantity=po.ordered_quantity, 
        job_type=job_type
      )
  except IntegrityError:
    db.rollback()
    logger.exception("Integrity error creating production order")
    return ProductionOrderCreatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Could not create ProductionOrder: a database constraint was violated",
      ),
    )
  except SQLAlchemyError:
    db.rollback()
    logger.exception("Database error creating production order")
    return ProductionOrderCreatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Could not create ProductionOrder due to a database error",
      ),
    )
    
  db.refresh(po)
      
  return ProductionOrderCreatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrder {po_number} for {eliquid.description} created"
    )
  )

def create_production_order_activity_log(
  db: Session,
  production_order_id: uuid.UUID,
  type: ProductionOrderActivityType,
  triggered_at: datetime,
  old_value: Optional[str],
  new_value: Optional[str],
) -> ProductionOrderActivityLog:
  # this mutation is called internally on every update of ProductionOrder
  # doesn't need graphql schema, input, and payload type
  
  log = ProductionOrderActivityLog(
    production_order_id=production_order_id,
    type=type,
    triggered_at=triggered_at,
    old_value=old_value,
    new_value=new_value,
  )
    
  db.add(log)
  db.flush()
  
  return log

def create_production_order_allocation(
  db: Session,
  production_order_id: uuid.UUID,
  location_id: uuid.UUID,
  quantity: int,
) -> ProductionOrderAllocation:
  allocation = ProductionOrderAllocation(
    production_order_id=production_order_id,
    location_id=location_id,
    quantity=quantity
  )
  
  db.add(allocation)
  db.flush()
  
  return allocation

def create_mix_job(db: Session, production_order: ProductionOrder, ordered_quantity: int, created_at: datetime) -> ProductionOrderJobCreatePayload:
  sequence = db.scalar(
    select(func.count()).select_from(MixJob).where(MixJob.production_order_id == production_order.id)
  ) + 1
  
  po_job = MixJob(
    job_number=generate_job_number(production_order.order_number, "MJ", sequence),
    production_order_id=production_order.id,
    ordered_quantity=ordered_quantity,
    created_at=created_at,
    updated_at=created_at,
  )
  
  db.add(po_job)
  db.flush()
  
  return ProductionOrderJobCreatePayload(
    production_order_job=MixJobType.from_model(po_job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

# def create_repat_job(db: Session, production_order: ProductionOrder, ordered_quantity: Optional[int], created_at: datetime) -> ProductionOrderJobCreatePayload:
#   sequence = db.scalar(
#     select(func.count()).select_from(RepatJob).where(RepatJob.production_order_id == production_order.id)
#   ) + 1
  
#   po_job = RepatJob(
#     job_number=generate_job_number(production_order.order_number, "RJ", sequence),
#     production_order_id=production_order.id,
#     ordered_quantity=ordered_quantity,
#     created_at=created_at,
#     updated_at=created_at,
#   )
  
#   db.add(po_job)
#   db.flush()
  
#   return ProductionOrderJobCreatePayload(
#     production_order_job=RepatJobType.from_model(po_job),
#     feedback=Feedback(
#       status=FeedbackStatusEnum.SUCCESS,
#       message=None,
#     )
#   )
  
def delete_production_order(db: Session, identifier: "ProductionOrderIdentifierInput") -> ProductionOrderDeletePayload:
  po = get_production_order(db=db, identifier=identifier)
  
  if po is None:
    return ProductionOrderDeletePayload(
      deleted_order_number=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} not found."
      )
    )
  
  order_number = po.order_number
  
  db.delete(po)
  db.commit()
  
  return ProductionOrderDeletePayload(
    deleted_order_number=order_number,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None
    )
  )

def mark_production_order_cancelled(db: Session, identifier: "ProductionOrderIdentifierInput") -> ProductionOrderUpdatePayload:
  po = db.scalar(select(ProductionOrder).where(identifier.query_condition))
  
  if po is None:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} not found"
      )
    )
  
  if po.status != ProductionOrderStatus.PENDING and po.status != ProductionOrderStatus.IN_PROGRESS:
    return ProductionOrderAssignJobPayload(
      production_order=ProductionOrderType.from_model(po),
      created_production_order_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Cannot cancel ProductionOrder {identifier.provided[1]} in {po.status.name} status"
      )
    )
    
  old_value = f"{po.status.name}"
  
  today = get_today("UTC")
  
  po.status = ProductionOrderStatus.CANCELLED
  po.updated_at = today
  db.flush()
  
  current_job = po.current_job
  
  if po.job_type == ProductionOrderJobType.MIX and current_job is not None:
    mark_mix_job_cancelled(
      db=db, 
      identifier=MixJobIdentifierInput(job_number=current_job.job_number),
    )
  # elif po.job_type == ProductionOrderJobType.REPAT and current_job is not None:
  #   mark_repat_job_cancelled(
  #     db=db, 
  #     identifier=RepatJobIdentifierInput(job_number=current_job.job_number),
  #   )
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    type=ProductionOrderActivityType.CHANGE_STATUS,
    triggered_at=today,
    old_value=old_value,
    new_value=f"{po.status.name}",
  )
  
  db.commit()
  db.refresh(po)
    
  return ProductionOrderUpdatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrder {po.order_number} cancelled"
    )
  )

def mark_production_order_delivered(db: Session, identifier: "ProductionOrderIdentifierInput") -> ProductionOrderUpdatePayload:
  po = db.scalar(select(ProductionOrder).where(identifier.query_condition))
  
  if po is None:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} not found"
      )
    )
  
  if po.status == ProductionOrderStatus.DELIVERED:
    return ProductionOrderUpdatePayload(
      production_order=ProductionOrderType.from_model(po),
      feedback=Feedback(
        status=FeedbackStatusEnum.SUCCESS,
        message=f"ProductionOrder {po.order_number} is already delivered"
      )
    )
    
  old_value = f"{po.status.name}"
  
  today = get_today("UTC")
  
  po.status = ProductionOrderStatus.DELIVERED
  po.updated_at = today
  db.flush()
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    type=ProductionOrderActivityType.CHANGE_STATUS,
    triggered_at=today,
    old_value=old_value,
    new_value=f"{po.status.name}",
  )
  
  db.commit()
  db.refresh(po)
    
  return ProductionOrderUpdatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrder {po.order_number} delivered"
    )
  )

def mark_production_order_fulfilled(db: Session, identifier: "ProductionOrderIdentifierInput", fulfilled_quantity: int) -> ProductionOrderUpdatePayload:
  po = db.scalar(
    select(ProductionOrder).where(
      and_(
        identifier.query_condition,
        ProductionOrder.status == ProductionOrderStatus.IN_PROGRESS,
      )
    )
  )
  
  if po is None:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} in progress not found"
      )
    )
  
  old_value = f"{po.status.name}"
  
  today_as_utc = get_today("UTC")
  
  po.fulfilled_quantity = fulfilled_quantity
  po.status = ProductionOrderStatus.FULFILLED
  po.updated_at = today_as_utc
  db.flush()
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    type=ProductionOrderActivityType.CHANGE_STATUS,
    triggered_at=today_as_utc,
    old_value=old_value,
    new_value=f"{po.status.name}",
  )
  
  db.commit()
  db.refresh(po)
    
  return ProductionOrderUpdatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrder {po.order_number} fulfilled"
    )
  )
  
def mark_production_order_in_progress(db: Session, identifier: "ProductionOrderIdentifierInput") -> ProductionOrderUpdatePayload:
  po = db.scalar(
    select(ProductionOrder).where(
      and_(
        identifier.query_condition,
        ProductionOrder.status == ProductionOrderStatus.PENDING,
      )
    )
  )
  
  if po is None:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} pending not found"
      )
    )
  
  old_value = f"{po.status.name}"
  
  today_as_utc = get_today("UTC")
  
  po.status = ProductionOrderStatus.IN_PROGRESS
  po.updated_at = today_as_utc
  db.flush()
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    type=ProductionOrderActivityType.CHANGE_STATUS,
    triggered_at=today_as_utc,
    old_value=old_value,
    new_value=f"{po.status.name}",
  )
  
  db.commit()
  db.refresh(po)
    
  return ProductionOrderUpdatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrder {po.order_number} in progress"
    )
  )

def mark_mix_job_cancelled(db: Session, identifier: "MixJobIdentifierInput") -> MixJobUpdatePayload:
  job = db.scalar(
    select(MixJob).where(
      and_(
        identifier.query_condition,
        MixJob.status == MixJobStatus.IN_PROGRESS,
      )
    )
  )
  
  if job is None:
    return MixJobUpdatePayload(
      mix_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"MixJob {identifier.provided[1]} with {MixJobStatus.IN_PROGRESS.name} status not found"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  job.status = MixJobStatus.CANCELLED
  job.updated_at = today_as_utc
  db.flush()
  
  return MixJobUpdatePayload(
    mix_job=MixJobType.from_model(job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"MixJob {job.job_number} cancelled",
    )
  )

def mark_mix_job_completed(db: Session, identifier: "MixJobIdentifierInput") -> MixJobUpdatePayload:
  job = db.scalar(
    select(MixJob).where(
      and_(
        identifier.query_condition,
        MixJob.status == MixJobStatus.MIXED,
      )
    )
  )
  
  if job is None:
    return MixJobUpdatePayload(
      mix_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"MixJob {identifier.provided[1]} mixed not found"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  job.status = MixJobStatus.COMPLETED
  job.updated_at = today_as_utc
  
  db.flush()
  
  mark_production_order_fulfilled(db=db, identifier=ProductionOrderIdentifierInput(order_number=job.production_order.order_number), fulfilled_quantity=job.produced_quantity)
 
  db.commit()
  db.refresh(job)
    
  return MixJobUpdatePayload(
    mix_job=MixJobType.from_model(job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"MixJob {job.job_number} completed"
    )
  )
  
def mark_mix_job_mixed(db: Session, identifier: "MixJobIdentifierInput", input: "MixJobMarkMixedInput") -> MixJobUpdatePayload:
  job = db.scalar(
    select(MixJob).where(
      and_(
        identifier.query_condition,
        MixJob.status == MixJobStatus.IN_PROGRESS,
      )
    )
  )
  
  if job is None:
    return MixJobUpdatePayload(
      mix_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"MixJob {identifier.provided[1]} in progress not found"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  job.status = MixJobStatus.MIXED
  
  job.produced_quantity = input.produced_quantity
  
  recipe = input.recipe
  job.recipe_snapshot = convert_strawberry_input_to_dict(recipe)
  job.total_volume_ml = recipe.total_volume_ml
  job.total_weight_g = recipe.total_weight_g
  
  job.updated_at = today_as_utc

  db.commit()
  db.refresh(job)
    
  return MixJobUpdatePayload(
    mix_job=MixJobType.from_model(job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"MixJob {job.job_number} mixed"
    )
  )
  
def mark_mix_job_reassigned(db: Session, identifier: "MixJobIdentifierInput", ) -> MixJobUpdatePayload:
  job = db.scalar(
    select(MixJob).where(
      and_(
        identifier.query_condition,
        MixJob.status == MixJobStatus.IN_PROGRESS,
      )
    )
  )
  
  if job is None:
    return MixJobUpdatePayload(
      mix_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"MixJob {identifier.provided[1]} with {MixJobStatus.IN_PROGRESS.name} status not found"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  job.status = MixJobStatus.REASSIGNED
  job.updated_at = today_as_utc
  db.flush()
  
  return MixJobUpdatePayload(
    mix_job=MixJobType.from_model(job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None
    )
  )

# def mark_repat_job_cancelled(db: Session, identifier: "RepatJobIdentifierInput") -> RepatJobUpdatePayload:
#   job = db.scalar(
#     select(RepatJob).where(
#       and_(
#         identifier.query_condition,
#         RepatJob.status == RepatJobStatus.IN_PROGRESS,
#       )
#     )
#   )
  
#   if job is None:
#     return RepatJobUpdatePayload(
#       repat_job=None,
#       feedback=Feedback(
#         status=FeedbackStatusEnum.FAILED,
#         message=f"RepatJob {identifier.provided[1]} with {RepatJobStatus.IN_PROGRESS.name} status not found"
#       )
#     )
  
#   today_as_utc = get_today("UTC")
  
#   job.status = RepatJobStatus.CANCELLED
#   job.updated_at = today_as_utc
#   db.flush()
    
#   return RepatJobUpdatePayload(
#     repat_job=RepatJobType.from_model(job),
#     feedback=Feedback(
#       status=FeedbackStatusEnum.SUCCESS,
#       message=f"RepatJob {job.job_number} cancelled"
#     )
#   )

# def mark_repat_job_completed(db: Session, identifier: "RepatJobIdentifierInput", input: "RepatJobMarkCompletedInput") -> RepatJobUpdatePayload:
#   job = db.scalar(
#     select(RepatJob).where(
#       and_(
#         identifier.query_condition,
#         RepatJob.status == RepatJobStatus.IN_PROGRESS,
#       )
#     )
#   )
  
#   if job is None:
#     return RepatJobUpdatePayload(
#       repat_job=None,
#       feedback=Feedback(
#         status=FeedbackStatusEnum.FAILED,
#         message=f"RepatJob {identifier.provided[1]} with {RepatJobStatus.IN_PROGRESS.name} status not found"
#       )
#     )
  
#   today_as_utc = get_today("UTC")
  
#   job.status = RepatJobStatus.COMPLETED
  
#   job.incoming_quantity = input.incoming_quantity
  
#   job.updated_at = today_as_utc
  
#   db.flush()
  
#   mark_production_order_fulfilled(
#     db=db, 
#     identifier=ProductionOrderIdentifierInput(order_number=job.production_order.order_number), 
#     fulfilled_quantity=job.incoming_quantity,
#   )
 
#   db.commit()
#   db.refresh(job)
    
#   return RepatJobUpdatePayload(
#     repat_job=RepatJobType.from_model(job),
#     feedback=Feedback(
#       status=FeedbackStatusEnum.SUCCESS,
#       message=f"RepatJob {job.job_number} completed"
#     )
#   )

# def mark_repat_job_reassigned(db: Session, identifier: "RepatJobIdentifierInput") -> RepatJobUpdatePayload:
#   job = db.scalar(
#     select(RepatJob).where(
#       and_(
#         identifier.query_condition,
#         RepatJob.status == RepatJobStatus.IN_PROGRESS,
#       )
#     )
#   )
  
#   if job is None:
#     return RepatJobUpdatePayload(
#       repat_job=None,
#       feedback=Feedback(
#         status=FeedbackStatusEnum.FAILED,
#         message=f"RepatJob {identifier.provided[1]} not found"
#       )
#     )
  
#   today_as_utc = get_today("UTC")
  
#   job.status = RepatJobStatus.REASSIGNED
#   job.updated_at = today_as_utc
#   db.flush()
  
#   return RepatJobUpdatePayload(
#     repat_job=RepatJobType.from_model(job),
#     feedback=Feedback(
#       status=FeedbackStatusEnum.SUCCESS,
#       message=None
#     )
#   )
  

def set_production_order_archived(db: Session, identifier: "ProductionOrderIdentifierInput", is_archived: bool) -> ProductionOrderUpdatePayload:
  po = db.scalar(select(ProductionOrder).where(identifier.query_condition))
  
  if po is None:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} not found"
      )
    )
  
  if po.is_archived == is_archived:
    return ProductionOrderUpdatePayload(
      production_order=ProductionOrderType.from_model(po),
      feedback=Feedback(
        status=FeedbackStatusEnum.SUCCESS,
        message=f"ProductionOrder {po.order_number} is already {'archived' if is_archived else 'unarchived'}"
      )
    )
    
  old_value = f"{po.is_archived}"
  
  today = get_today("UTC")
  
  po.is_archived = is_archived
  po.updated_at = today
  db.flush()
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    type=ProductionOrderActivityType.TOGGLE_ARCHIVED,
    triggered_at=today,
    old_value=old_value,
    new_value=f"{po.is_archived}",
  )
  
  db.commit()
  db.refresh(po)
    
  return ProductionOrderUpdatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrder {po.order_number} {'archived' if po.is_archived else 'unarchived'}"
    )
  )

def set_production_order_priority(db: Session, identifier: "ProductionOrderIdentifierInput", is_priority: bool) -> ProductionOrderUpdatePayload:
  po = db.scalar(select(ProductionOrder).where(identifier.query_condition))
  
  if po is None:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} not found"
      )
    )
  
  if po.is_priority == is_priority:
    return ProductionOrderUpdatePayload(
      production_order=ProductionOrderType.from_model(po),
      feedback=Feedback(
        status=FeedbackStatusEnum.SUCCESS,
        message=f"ProductionOrder {po.order_number} is already {'priority' if is_priority else 'not priority'}"
      )
    )
    
  old_value = f"{po.is_priority}"
  
  today = get_today("UTC")
  
  po.is_priority = is_priority
  po.updated_at = today
  db.flush()
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    type=ProductionOrderActivityType.SWITCH_PRIORITY,
    triggered_at=today,
    old_value=old_value,
    new_value=f"{po.is_priority}",
  )
  
  db.commit()
  db.refresh(po)
    
  return ProductionOrderUpdatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrder {po.order_number} {'set as priority' if po.is_priority else 'unset as priority'}"
    )
  )

def set_production_order_ordered_quantity(db: Session, identifier: "ProductionOrderIdentifierInput", ordered_quantity: int | None) -> ProductionOrderUpdatePayload:
  po = db.scalar(select(ProductionOrder).where(identifier.query_condition))
  
  if po is None:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} not found"
      )
    )
  
  if ordered_quantity == po.ordered_quantity:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"Quantity {ordered_quantity} is the same"
      )
    )
  
  if po.allocated_quantity > 0:
    allocated = po.allocated_quantity
    if ordered_quantity is None or ordered_quantity < allocated:
      return ProductionOrderUpdatePayload(
        production_order=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message=f"Ordered quantity ({ordered_quantity}) cannot be less than allocated quantity ({allocated})"
        )
      )
    
  
  old_value = f"{po.ordered_quantity}"
  
  today = get_today("UTC")
  
  po.ordered_quantity = ordered_quantity
  po.updated_at = today
  db.flush()
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    type=ProductionOrderActivityType.ADJUST_QUANTITY,
    triggered_at=today,
    old_value=old_value,
    new_value=f"{po.ordered_quantity}",
  )
  
  db.commit()
  db.refresh(po)
    
  return ProductionOrderUpdatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrder {po.order_number} quantity updated to {po.ordered_quantity}"
    )
  )
  
def update_production_order(db: Session, identifier: "ProductionOrderIdentifierInput", input: "ProductionOrderUpdateInput") -> ProductionOrderUpdatePayload:
  po = db.scalar(select(ProductionOrder).where(identifier.query_condition))
  
  if po is None:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} not found"
      )
    )
  
  updated_columns = []  
  
  for attr, value in vars(input).items():
    today = get_today("UTC")
    
    current = getattr(po, attr, None)
    
    if value is strawberry.UNSET:
      continue
    if isinstance(value, Enum):
      value = value.name
      current = current.name if current else None
    
    if value != current:
      setattr(po, attr, value)
      po.updated_at = today
      db.flush()
      
      create_production_order_activity_log(
        db=db,
        production_order_id=po.id,
        type=ProductionOrderActivityType(attr),
        triggered_at=today,
        old_value=f"{current.name}",
        new_value=f"{value}",
      )
      
      updated_columns.append(attr)
  
  if len(updated_columns) == 0:
    message = "Nothing to update"
  else:
    db.commit()
    db.refresh(po)
    
    message = f"Updated {', '.join(updated_columns)}"
  
  return ProductionOrderUpdatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=message
    )
  )