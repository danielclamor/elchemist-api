from datetime import datetime
from typing import List
import uuid

import strawberry
from strawberry import relay

from api_graphql.types.enums import ProductionOrderActivity, ProductionOrderStatus

@strawberry.type
class ProductionOrderActivityLog(relay.Node):
  id: uuid.UUID
  activity: ProductionOrderActivity
  old_value: str
  new_value: str
  triggered_at: datetime

@strawberry.type
class ProductionOrderType(relay.Node):
  order_number: str
  eliquid_id: uuid.UUID
  eliquid_description: str
  quantity: int
  status: ProductionOrderStatus
  is_priority: bool
  created_at: datetime
  activity_logs: List[ProductionOrderActivityLog]