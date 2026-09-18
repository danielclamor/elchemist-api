from __future__ import annotations

from datetime import datetime
from enum import Enum
import uuid

import strawberry

from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from zoneinfo import ZoneInfo

from models import (
  Eliquid,
  ProductionOrder,
  ProductionOrderJob,
  ProductionOrderMixJob,
  ProductionOrderMixJobStatus,
  ProductionOrderRepatJob,
  ProductionOrderRepatJobStatus,
  ProductionOrderStatus,
  ProductionOrderActivityLog,
  ProductionOrderActivity,
  ProductionOrderCounter,
)

from api_graphql.types.feedback import Feedback, FeedbackStatusEnum

from api_graphql.types.eliquid import EliquidIdentifierInput

from api_graphql.types.production_order import (
  ProductionOrderAssignJobPayload,
  ProductionOrderJobCreatePayload,
  ProductionOrderMixJobType,
  ProductionOrderMixJobUpdatePayload,
  ProductionOrderRepatJobType,
  ProductionOrderRepatJobUpdatePayload,
  ProductionOrderType,
  ProductionOrderCreatePayload,
  ProductionOrderDeletePayload,
  ProductionOrderUpdatePayload,
)

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
  from api_graphql.types.production_order import (
    ProductionOrderIdentifierInput,
    ProductionOrderMixJobIdentifierInput,
    ProductionOrderRepatJobIdentifierInput,
    ProductionOrderMixJobMarkMixedInput,
    ProductionOrderCreateInput,
    ProductionOrderUpdateInput,
  )
  
  from api_graphql.types.enums import ProductionOrderJobEnum

from .utils import generate_production_order_number, get_today, convert_strawberry_input_to_dict

# Queries
def get_all_production_orders(db: Session) -> list[ProductionOrder]:
  return (
    db.scalars(select(ProductionOrder)).unique().all()
  )

def get_all_production_order_mix_jobs(db: Session) -> list[ProductionOrderMixJob]:
  return (
    db.scalars(select(ProductionOrderMixJob)).unique().all()
  )
  
def get_all_production_order_repat_jobs(db: Session) -> list[ProductionOrderRepatJob]:
  return (
    db.scalars(select(ProductionOrderRepatJob)).unique().all()
  )

def get_production_order(db: Session, identifier: "ProductionOrderIdentifierInput") -> ProductionOrder | None:
  return (
    db.scalar(select(ProductionOrder).where(identifier.query_condition))
  )
  
def get_production_order_mix_job(db: Session, identifier: "ProductionOrderMixJobIdentifierInput") -> ProductionOrderMixJob | None:
  return (
    db.scalar(select(ProductionOrderMixJob).where(identifier.query_condition))
  )

def get_production_order_repat_job(db: Session, identifier: "ProductionOrderRepatJobIdentifierInput") -> ProductionOrderRepatJob | None:
  return (
    db.scalar(select(ProductionOrderRepatJob).where(identifier.query_condition))
  )

# Mutations    
def assign_production_order_job(db: Session, identifier: "ProductionOrderIdentifierInput", job: "ProductionOrderJobEnum") -> ProductionOrderAssignJobPayload:
  po = db.scalar(select(ProductionOrder).where(identifier.query_condition))

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
    
  old_job = po.job
  new_job = ProductionOrderJob[job.name]
  
  if old_job == new_job:
    return ProductionOrderAssignJobPayload(
      production_order=ProductionOrderType.from_model(po),
      created_production_order_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"ProductionOrder {identifier.provided[1]} is already assigned to {job.name}"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  if old_job == ProductionOrderJob.MIX:
    reassigned_job = mark_production_order_mix_job_reassigned(
      db=db,
      production_order_number=po.order_number,
    ).production_order_mix_job
  elif old_job == ProductionOrderJob.REPAT:
    reassigned_job = mark_production_order_repat_job_reassigned(
      db=db,
      production_order_number=po.order_number,
    ).production_order_repat_job
  else:
    reassigned_job = None
    
  if old_job is not None and reassigned_job is None:
    return ProductionOrderAssignJobPayload(
      production_order=ProductionOrderType.from_model(po),
      created_production_order_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Failed to reassign ProductionOrder {identifier.provided[1]} old {old_job} job"
      )
    )
   
  if new_job == ProductionOrderJob.MIX:
    created_job = create_production_order_mix_job(
      db=db,
      production_order=po,
      created_at=today_as_utc,
    ).production_order_job
  elif new_job == ProductionOrderJob.REPAT:
    created_job = create_production_order_repat_job(
      db=db,
      production_order=po,
      created_at=today_as_utc,
    ).production_order_job
  else:
    return ProductionOrderAssignJobPayload(
      production_order=None,
      created_production_order_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Job type not supported"
      )
    )
    
  po.job = new_job
  db.flush()
  
  create_production_order_activity_log(
    db=db, 
    production_order_id=po.id,
    activity=ProductionOrderActivity.ASSIGN_JOB,
    triggered_at=today_as_utc,
    old_value=f"{old_job.name if old_job is not None else None}",
    new_value=f"{new_job.name}"
  )
  
  from api_graphql.types.production_order import ProductionOrderIdentifierInput
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
  
  today = get_today()
  todate = today.date()
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
  
  created_at_utc = today.astimezone(ZoneInfo("UTC"))
  
  po = ProductionOrder(
    order_number=po_number,
    eliquid_id=eliquid.id,
    quantity=input.quantity,
    is_priority=input.is_priority,
    status=ProductionOrderStatus.PENDING,
    created_at=created_at_utc,
    updated_at=created_at_utc,
  )
  
  db.add(po)
  db.flush()
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    activity=ProductionOrderActivity.CREATED,
    triggered_at=created_at_utc,
    old_value=None,
    new_value=None,
  )
  
  db.commit()
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
  activity: ProductionOrderActivity,
  triggered_at: datetime,
  old_value: Optional[str],
  new_value: Optional[str],
) -> ProductionOrderActivityLog:
  # this mutation is called internally on every update of ProductionOrder
  # doesn't need graphql schema, input, and payload type
  
  log = ProductionOrderActivityLog(
    production_order_id=production_order_id,
    activity=activity,
    triggered_at=triggered_at,
    old_value=old_value,
    new_value=new_value,
  )
    
  db.add(log)
  db.flush()
  
  return log
  
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

def create_production_order_mix_job(db: Session, production_order: ProductionOrder, created_at: datetime) -> ProductionOrderJobCreatePayload:
  po_job = ProductionOrderMixJob(
    production_order_id=production_order.id,
    production_order_number=production_order.order_number,
    ordered_quantity=production_order.quantity,
    is_priority=production_order.is_priority,
    created_at=created_at,
    updated_at=created_at,
  )
  
  db.add(po_job)
  db.flush()
  
  return ProductionOrderJobCreatePayload(
    production_order_job=ProductionOrderMixJobType.from_model(po_job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def create_production_order_repat_job(db: Session, production_order: ProductionOrder, created_at: datetime) -> ProductionOrderJobCreatePayload:
  po_job = ProductionOrderRepatJob(
    production_order_id=production_order.id,
    production_order_number=production_order.order_number,
    ordered_quantity=production_order.quantity,
    created_at=created_at,
    updated_at=created_at,
  )
  
  db.add(po_job)
  db.flush()
  
  return ProductionOrderJobCreatePayload(
    production_order_job=ProductionOrderRepatJobType.from_model(po_job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
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
  
  if po.job == ProductionOrderJob.MIX:
    from api_graphql.types.production_order import ProductionOrderMixJobIdentifierInput
    mark_production_order_mix_job_cancelled(
      db=db, 
      identifier=ProductionOrderMixJobIdentifierInput(production_order_number=po.order_number),
    )
  elif po.job == ProductionOrderJob.REPAT:
    from api_graphql.types.production_order import ProductionOrderRepatJobIdentifierInput
    mark_production_order_repat_job_cancelled(
      db=db, 
      identifier=ProductionOrderRepatJobIdentifierInput(production_order_number=po.order_number),
    )
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    activity=ProductionOrderActivity.CHANGE_STATUS,
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
    activity=ProductionOrderActivity.DELIVERED,
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

def mark_production_order_fulfilled(db: Session, identifier: "ProductionOrderIdentifierInput") -> ProductionOrderUpdatePayload:
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
  
  po.status = ProductionOrderStatus.FULFILLED
  po.updated_at = today_as_utc
  db.flush()
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    activity=ProductionOrderActivity.CHANGE_STATUS,
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
    activity=ProductionOrderActivity.CHANGE_STATUS,
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

def mark_production_order_mix_job_cancelled(db: Session, identifier: "ProductionOrderMixJobIdentifierInput") -> ProductionOrderMixJobUpdatePayload:
  job = db.scalar(
    select(ProductionOrderMixJob).where(
      and_(
        identifier.query_condition,
        ProductionOrderMixJob.status == ProductionOrderMixJobStatus.IN_PROGRESS,
      )
    )
  )
  
  if job is None:
    return ProductionOrderMixJobUpdatePayload(
      production_order_mix_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrderMixJob {identifier.provided[1]} with {ProductionOrderMixJobStatus.IN_PROGRESS.name} status not found"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  job.status = ProductionOrderMixJobStatus.CANCELLED
  job.updated_at = today_as_utc
  db.flush()
  
  return ProductionOrderMixJobUpdatePayload(
    production_order_mix_job=ProductionOrderMixJobType.from_model(job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None
    )
  )

def mark_production_order_mix_job_completed(db: Session, identifier: "ProductionOrderMixJobIdentifierInput") -> ProductionOrderMixJobUpdatePayload:
  job = db.scalar(
    select(ProductionOrderMixJob).where(
      and_(
        identifier.query_condition,
        ProductionOrderMixJob.status == ProductionOrderMixJobStatus.MIXED,
      )
    )
  )
  
  if job is None:
    return ProductionOrderMixJobUpdatePayload(
      production_order_mix_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrderMixJob {identifier.provided[1]} mixed not found"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  job.status = ProductionOrderMixJobStatus.COMPLETED
  job.updated_at = today_as_utc
  
  db.flush()
  
  from api_graphql.types.production_order import ProductionOrderIdentifierInput
  mark_production_order_fulfilled(db=db, identifier=ProductionOrderIdentifierInput(order_number=job.production_order_number))
 
  db.commit()
  db.refresh(job)
    
  return ProductionOrderMixJobUpdatePayload(
    production_order_mix_job=ProductionOrderMixJobType.from_model(job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrderMixJob {job.production_order_number} completed"
    )
  )
  
def mark_production_order_mix_job_mixed(db: Session, identifier: "ProductionOrderMixJobIdentifierInput", input: "ProductionOrderMixJobMarkMixedInput") -> ProductionOrderMixJobUpdatePayload:
  job = db.scalar(
    select(ProductionOrderMixJob).where(
      and_(
        identifier.query_condition,
        ProductionOrderMixJob.status == ProductionOrderMixJobStatus.IN_PROGRESS,
      )
    )
  )
  
  if job is None:
    return ProductionOrderMixJobUpdatePayload(
      production_order_mix_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrderMixJob {identifier.provided[1]} in progress not found"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  job.status = ProductionOrderMixJobStatus.MIXED
  
  job.produced_quantity = input.produced_quantity
  
  recipe = input.recipe
  job.recipe_snapshot = convert_strawberry_input_to_dict(recipe)
  job.total_volume_ml = recipe.total_volume_ml
  job.total_weight_g = recipe.total_weight_g
  
  job.updated_at = today_as_utc

  db.commit()
  db.refresh(job)
    
  return ProductionOrderMixJobUpdatePayload(
    production_order_mix_job=ProductionOrderMixJobType.from_model(job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrderMixJob {job.production_order_number} mixed"
    )
  )
  
def mark_production_order_mix_job_reassigned(db: Session, production_order_number: str) -> ProductionOrderMixJobUpdatePayload:
  job = db.scalar(
    select(ProductionOrderMixJob).where(
      and_(
        ProductionOrderMixJob.production_order_number == production_order_number,
        ProductionOrderMixJob.status == ProductionOrderMixJobStatus.IN_PROGRESS,
      )
    )
  )
  
  if job is None:
    return ProductionOrderMixJobUpdatePayload(
      production_order_mix_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrderMixJob {production_order_number} with {ProductionOrderMixJobStatus.IN_PROGRESS.name} status not found"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  job.status = ProductionOrderMixJobStatus.REASSIGNED
  job.updated_at = today_as_utc
  db.flush()
  
  return ProductionOrderMixJobUpdatePayload(
    production_order_mix_job=ProductionOrderMixJobType.from_model(job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None
    )
  )

def mark_production_order_repat_job_cancelled(db: Session, identifier: "ProductionOrderRepatJobIdentifierInput") -> ProductionOrderRepatJobUpdatePayload:
  job = db.scalar(
    select(ProductionOrderRepatJob).where(
      and_(
        identifier.query_condition,
        ProductionOrderRepatJob.status == ProductionOrderRepatJobStatus.IN_PROGRESS,
      )
    )
  )
  
  if job is None:
    return ProductionOrderRepatJobUpdatePayload(
      production_order_mix_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrderRepatJob {identifier.provided[1]} with {ProductionOrderRepatJobStatus.IN_PROGRESS.name} status not found"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  job.status = ProductionOrderRepatJobStatus.CANCELLED
  job.updated_at = today_as_utc
  
  db.flush()
  
  from api_graphql.types.production_order import ProductionOrderIdentifierInput
  mark_production_order_fulfilled(db=db, identifier=ProductionOrderIdentifierInput(order_number=job.production_order_number))
 
  db.commit()
  db.refresh(job)
    
  return ProductionOrderRepatJobUpdatePayload(
    production_order_mix_job=ProductionOrderRepatJobType.from_model(job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrderRepatJob {job.production_order_number} cancelled"
    )
  )

def mark_production_order_repat_job_completed(db: Session, identifier: "ProductionOrderRepatJobIdentifierInput") -> ProductionOrderRepatJobUpdatePayload:
  job = db.scalar(
    select(ProductionOrderRepatJob).where(
      and_(
        identifier.query_condition,
        ProductionOrderRepatJob.status == ProductionOrderRepatJobStatus.IN_PROGRESS,
      )
    )
  )
  
  if job is None:
    return ProductionOrderRepatJobUpdatePayload(
      production_order_mix_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrderRepatJob {identifier.provided[1]} with {ProductionOrderRepatJobStatus.IN_PROGRESS.name} status not found"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  job.status = ProductionOrderRepatJobStatus.COMPLETED
  job.updated_at = today_as_utc
  
  db.flush()
  
  from api_graphql.types.production_order import ProductionOrderIdentifierInput
  mark_production_order_fulfilled(db=db, identifier=ProductionOrderIdentifierInput(order_number=job.production_order_number))
 
  db.commit()
  db.refresh(job)
    
  return ProductionOrderRepatJobUpdatePayload(
    production_order_mix_job=ProductionOrderRepatJobType.from_model(job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrderRepatJob {job.production_order_number} completed"
    )
  )

def mark_production_order_repat_job_reassigned(db: Session, production_order_number: str) -> ProductionOrderRepatJobUpdatePayload:
  job = db.scalar(
    select(ProductionOrderRepatJob).where(
      and_(
        ProductionOrderRepatJob.production_order_number == production_order_number,
        ProductionOrderRepatJob.status == ProductionOrderRepatJobStatus.IN_PROGRESS,
      )
    )
  )
  
  if job is None:
    return ProductionOrderRepatJobUpdatePayload(
      production_order_repat_job=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrderRepatJob {production_order_number} not found"
      )
    )
  
  today_as_utc = get_today("UTC")
  
  job.status = ProductionOrderRepatJobStatus.REASSIGNED
  job.updated_at = today_as_utc
  db.flush()
  
  return ProductionOrderRepatJobUpdatePayload(
    production_order_repat_job=ProductionOrderRepatJobType.from_model(job),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None
    )
  )
  

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
    activity=ProductionOrderActivity.TOGGLE_ARCHIVED,
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
    activity=ProductionOrderActivity.SWITCH_PRIORITY,
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

def set_production_order_quantity(db: Session, identifier: "ProductionOrderIdentifierInput", quantity: int) -> ProductionOrderUpdatePayload:
  po = db.scalar(select(ProductionOrder).where(identifier.query_condition))
  
  if po is None:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} not found"
      )
    )
  
  old_value = f"{po.quantity}"
  
  today = get_today("UTC")
  
  po.quantity = quantity
  po.updated_at = today
  db.flush()
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    activity=ProductionOrderActivity.ADJUST_QUANTITY,
    triggered_at=today,
    old_value=old_value,
    new_value=f"{po.quantity}",
  )
  
  db.commit()
  db.refresh(po)
    
  return ProductionOrderUpdatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=f"ProductionOrder {po.order_number} quantity updated to {po.quantity}"
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
        activity=ProductionOrderActivity(attr),
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