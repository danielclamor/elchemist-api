from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import select

from zoneinfo import ZoneInfo

import models

from api_graphql.types.feedback import Feedback, FeedbackStatus
from api_graphql.types.production_order import (
  ProductionOrderType,
  ProductionOrderCreatePayload,
  ProductionOrderDeletePayload,
  ProductionOrderUpdatePayload,
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from api_graphql.types.production_order import (
    ProductionOrderCreateInput,
    ProductionOrderDeleteInput,
    ProductionOrderUpdateIdentifier,
    ProductionOrderUpdateInput,
  )

from .utils import generate_production_order_number, get_today

# Queries
def get_all_production_orders(db: Session) -> list[models.ProductionOrder]:
  return (
    db.scalars(select(models.ProductionOrder)).unique().all()
  )

def get_production_order(db: Session, order_number: str) -> models.ProductionOrder:
  return (
    db.scalar(select(models.ProductionOrder).where(models.ProductionOrder.order_number == order_number))
  )


# Mutations
def create_production_order_activity_log(
  # this mutation is called internally on every update of ProductionOrder
  # doesn't need graphql schema, input, and payload type
  db: Session,
  production_order_id: uuid.UUID,
  activity: models.ProductionOrderActivity,
  triggered_at: datetime,
  old_value: str | None = None,
  new_value: str | None = None,
) -> models.ProductionOrderActivityLog:
  log = models.ProductionOrderActivityLog(
    production_order_id=production_order_id,
    activity=activity,
    triggered_at=triggered_at,
    old_value=old_value,
    new_value=new_value,
  )
    
  db.add(log)
  
  return log
  
def create_production_order(db: Session, input: "ProductionOrderCreateInput") -> ProductionOrderCreatePayload:
  eliquid = db.scalar(select(models.Eliquid).where(models.Eliquid.upc == input.eliquid_upc))
  if not eliquid:
    return ProductionOrderCreatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Eliquid {input.eliquid_upc} not found"
      )
    )
  
  today = get_today()
  todate = today.date()
  counter = db.scalar(
    select(models.ProductionOrderCounter)
    .where(models.ProductionOrderCounter.date == todate)
    .with_for_update()
  )

  if counter:
    counter.last_number += 1
  else:
    counter = models.ProductionOrderCounter(
      date=todate,
      last_number=1,
    )
    db.add(counter)

  db.flush()
  
  po_number = generate_production_order_number(date=todate, counter=counter.last_number)
  
  created_at_utc = today.astimezone(ZoneInfo("UTC"))
  
  po = models.ProductionOrder(
    order_number=po_number,
    eliquid_id=eliquid.id,
    quantity=input.quantity,
    is_priority=input.is_priority or False,
    created_at=created_at_utc,
    updated_at=created_at_utc,
  )
  
  db.add(po)
  db.flush()
  
  create_production_order_activity_log(
    db=db,
    production_order_id=po.id,
    activity=models.ProductionOrderActivity.CREATED,
    triggered_at=created_at_utc,
  )
  
  db.commit()
  db.refresh(po)
    
  return ProductionOrderCreatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=f"Production order {po_number} for {eliquid.description} created"
    )
  )
  
def delete_production_order(db: Session, input: "ProductionOrderDeleteInput") -> ProductionOrderDeletePayload:
  po = get_production_order(
    db=db,
    order_number=input.order_number,
  )
  
  if not po:
    return ProductionOrderDeletePayload(
      deleted_order_number=None,
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Production order {input.order_number} not found."
      )
    )
  
  db.delete(po)
  db.commit()
  
  return ProductionOrderDeletePayload(
    deleted_order_number=input.order_number,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None
    )
  )
  
def update_production_order(db: Session, identifier: ProductionOrderUpdateIdentifier, input: "ProductionOrderUpdateInput") -> ProductionOrderUpdatePayload:
  po = db.scalar(select(models.ProductionOrder).where(models.ProductionOrder.order_number == identifier.order_number))
  if not po:
    return ProductionOrderUpdatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Production order {identifier.order_number} not found"
      )
    )
  
  updated_columns = []  
  
  if input.status and input.status.value != po.status.value:
    today = get_today("UTC")
    old = po.status
    new = models.ProductionOrderStatus[input.status.name]
    
    po.status = new
    po.updated_at = today
    db.flush()
    
    create_production_order_activity_log(
      db=db,
      production_order_id=po.id,
      activity=models.ProductionOrderActivity.CHANGE_STATUS,
      triggered_at=today,
      old_value=f"{old.name}",
      new_value=f"{po.status.name}",
    )
    
    updated_columns.append("status")
  
  if input.quantity and input.quantity != po.quantity:
    today = get_today("UTC")
    old = po.quantity
    new = input.quantity
    
    po.quantity = new
    po.updated_at = today
    db.flush()
    
    create_production_order_activity_log(
      db=db,
      production_order_id=po.id,
      activity=models.ProductionOrderActivity.ADJUST_QUANTITY,
      triggered_at=today,
      old_value=f"{old}",
      new_value=f"{po.quantity}",
    )
      
    updated_columns.append("quantity")
      
  if input.is_priority and input.is_priority != po.is_priority:
    today = get_today("UTC")
    old = po.is_priority
    new = input.is_priority
    
    po.is_priority = new
    po.updated_at = today
    db.flush()
    
    create_production_order_activity_log(
      db=db,
      production_order_id=po.id,
      activity=models.ProductionOrderActivity.SWITCH_PRIORITY,
      triggered_at=today,
      old_value=f"{old}",
      new_value=f"{po.is_priority}",
    )
    
    updated_columns.append("isPriority")
  
  if len(updated_columns) > 0:
    db.commit()
    db.refresh(po)
    
    message = f"Updated {", ".join(updated_columns)}"
  else:
    message="Nothing to update"
  
  return ProductionOrderUpdatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=message
    )
  )