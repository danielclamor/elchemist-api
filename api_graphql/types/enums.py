import enum

import strawberry

@strawberry.enum
class ChillType(enum.Enum):
  CHILLED = "chilled"
  NON_CHILLED = "non-chilled"

@strawberry.enum
class NicType(enum.Enum):
  FREEBASE = "freebase"
  SALT = "salt"
  
@strawberry.enum
class SizeOption(enum.Enum):
  ML_30 = "30ml"
  ML_60 = "60ml"
  ML_120 = "120ml"

@strawberry.enum
class NicLevelOption(enum.Enum):
  MG_0 = "0mg"
  MG_3 = "3mg"
  MG_5 = "5mg"
  MG_6 = "6mg"
  MG_10 = "10mg"
  MG_12 = "12mg"
  MG_15 = "15mg"
  MG_18 = "18mg"
  MG_20 = "20mg"
  HIT_35 = "hit35"
  HIT_50 = "hit50"
  
@strawberry.enum
class BottleColor(enum.Enum):
  BLACK = "black"
  CLEAR = "clear"
  WHITE = "white"
  
@strawberry.enum
class ProductionOrderStatus(enum.Enum):
  CANCELLED = "cancelled"
  DELIVERED = "delivered"
  MIXED = "mixed"
  PENDING = "pending"
  
@strawberry.enum
class ProductionOrderActivity(enum.Enum):
  CREATED = "created"
  ADJUST_QUANTITY = "adjust_quantity"
  CHANGE_STATUS = "change_status"
  SWITCH_PRIORITY = "switch_priority"