from sqlalchemy.orm import Session
from sqlalchemy import select

from zoneinfo import ZoneInfo

import models

from api_graphql.types.enums import FeedbackStatus
from api_graphql.types.feedback import Feedback
from api_graphql.types.production_order import (
  ProductionOrderType,
  ProductionOrderCreateInput, 
  ProductionOrderCreatePayload,
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
def create_production_order(db: Session, production_order: ProductionOrderCreateInput) -> ProductionOrderCreatePayload:
  eliquid = db.scalar(select(models.Eliquid).where(models.Eliquid.upc == production_order.eliquid_upc))
  if not eliquid:
    return ProductionOrderCreatePayload(
      production_order=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Eliquid {production_order.eliquid_upc} not found"
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
  
  po = models.ProductionOrder(
    order_number=po_number,
    eliquid_id=eliquid.id,
    quantity=production_order.quantity,
    is_priority=production_order.is_priority or False,
    created_at=today.astimezone(ZoneInfo("UTC")),
    updated_at=today.astimezone(ZoneInfo("UTC")),
  )
  
  db.add(po)
  db.flush()
  db.refresh(po)
  
  l = models.ProductionOrderActivityLog(
    production_order_id=po.id,
    activity=models.ProductionOrderActivity.CREATED,
    triggered_at=today.astimezone(ZoneInfo("UTC")),
  )
  
  db.add(l)
  db.commit()
  
  return ProductionOrderCreatePayload(
    production_order=ProductionOrderType.from_model(po),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=f"Production order {po_number} for {eliquid.description} created"
    )
  )