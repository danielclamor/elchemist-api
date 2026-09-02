from __future__ import annotations

from datetime import datetime
from enum import Enum
import uuid

import strawberry

from sqlalchemy.orm import Session
from sqlalchemy import select

from zoneinfo import ZoneInfo

from models import (
  Eliquid,
  ProductionOrder,
  ProductionOrderStatus,
  ProductionOrderActivityLog,
  ProductionOrderActivity,
  ProductionOrderCounter,
)

from api_graphql.types.feedback import Feedback, FeedbackStatus

from api_graphql.types.eliquid import EliquidIdentifierInput

from api_graphql.types.production_order import (
  ProductionOrderType,
  ProductionOrderCreatePayload,
  ProductionOrderDeletePayload,
  ProductionOrderUpdatePayload,
)

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
  from api_graphql.types.production_order import (
    ProductionOrderIdentifierInput,
    ProductionOrderCreateInput,
    ProductionOrderUpdateInput,
  )

from .utils import generate_production_order_number, get_today

# Queries
def get_all_production_orders(db: Session) -> list[ProductionOrder]:
  return (
    db.scalars(select(ProductionOrder)).unique().all()
  )

def get_production_order(db: Session, identifier: ProductionOrderIdentifierInput) -> ProductionOrder:
  return (
    db.scalar(select(ProductionOrder).where(identifier.query_condition))
  )


# Mutations  
def create_production_order(db: Session, eliquid_identifier: "EliquidIdentifierInput", input: "ProductionOrderCreateInput") -> ProductionOrderCreatePayload: 
  eliquid = db.scalar(select(Eliquid).where(eliquid_identifier.query_condition))
  
  if eliquid is None:
    return ProductionOrderCreatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
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
      status=FeedbackStatus.SUCCESS,
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
        status=FeedbackStatus.FAILED,
        message=f"ProductionOrder {identifier.provided[1]} not found."
      )
    )
  
  order_number = po.order_number
  
  db.delete(po)
  db.commit()
  
  return ProductionOrderDeletePayload(
    deleted_order_number=order_number,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None
    )
  )
  
def update_production_order(db: Session, identifier: "ProductionOrderIdentifierInput", input: "ProductionOrderUpdateInput") -> ProductionOrderUpdatePayload:
  po = db.scalar(select(ProductionOrder).where(identifier.query_condition))
  
  if po is None:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
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
      status=FeedbackStatus.SUCCESS,
      message=message
    )
  )