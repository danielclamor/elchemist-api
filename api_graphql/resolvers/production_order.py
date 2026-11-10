from __future__ import annotations

import logging

from api_graphql.resolvers.mix_batch import change_mix_batch_status, create_mix_batch

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
  MixBatch,
  MixBatchStatus,
  ProductionOrder,
  ProductionOrderAllocation,
  ProductionOrderJobType,
  ProductionOrderStatus,
  ProductionOrderActivityLog,
  ProductionOrderActivityType,
  ProductionOrderCounter,
)

from api_graphql.types.feedback import Feedback, FeedbackStatusEnum

from api_graphql.types.eliquid import EliquidIdentifierInput

from api_graphql.types.production_order import (
  ProductionOrderIdentifierInput,
  ProductionOrderType,
  ProductionOrderCreatePayload,
  ProductionOrderDeletePayload,
  ProductionOrderUpdatePayload,
)

from api_graphql.types.enums import ProductionOrderJobTypeEnum

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
  from api_graphql.types.production_order import (
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
    )
    .order_by(ProductionOrder.created_at.desc(), ProductionOrder.id)
  )
  stmt = _filter_production_orders(stmt, job_type, status, created_from, created_to)
  return db.scalars(stmt).unique().all()

def get_production_order_status_counts(db: Session, created_from=None, created_to=None) -> dict:
  stmt = select(ProductionOrder.status, func.count()).group_by(ProductionOrder.status)
  stmt = _filter_production_orders(stmt, None, created_from, created_to)
  return {status: count for status, count in db.execute(stmt).all()}

def get_production_order(db: Session, identifier: "ProductionOrderIdentifierInput") -> ProductionOrder | None:
  return (
    db.scalar(select(ProductionOrder).where(identifier.query_condition))
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
    
  old_value = f"{po.status.name}"
  
  today = get_today("UTC")
  
  po.status = ProductionOrderStatus.CANCELLED
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

def remove_production_order_from_mix_batch(db: Session, production_order: ProductionOrder) -> None:
  batch = production_order.mix_batch
  production_order.mix_batch_id = None
  db.flush()
  remaining = db.scalar(select(func.count()).select_from(ProductionOrder).where(ProductionOrder.mix_batch_id == batch.id))
  if remaining == 0 and batch.status == MixBatchStatus.IN_PROGRESS:
    change_mix_batch_status(batch, MixBatchStatus.CANCELLED)
  
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