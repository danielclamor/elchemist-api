import enum

import strawberry

@strawberry.enum
class BottleColorEnum(enum.Enum):
  BLACK = "black"
  CLEAR = "clear"
  WHITE = "white"

@strawberry.enum
class ChillTypeEnum(enum.Enum):
  CHILLED = "chilled"
  NON_CHILLED = "non-chilled"

@strawberry.enum
class NicLevelOptionEnum(enum.Enum):
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
class NicTypeEnum(enum.Enum):
  FREEBASE = "freebase"
  SALT = "salt"
  
@strawberry.enum
class SizeOptionEnum(enum.Enum):
  ML_30 = "30ml"
  ML_60 = "60ml"
  ML_120 = "120ml"
  
@strawberry.enum
class ProductionOrderStatusEnum(enum.Enum):
  CANCELLED = "cancelled"
  DELIVERED = "delivered"
  FULFILLED = "fulfilled"
  IN_PROGRESS = "in_progress"
  PENDING = "pending"
  
@strawberry.enum
class ProductionOrderActivityEnum(enum.Enum):
  CREATED = "created"
  ADJUST_QUANTITY = "quantity"
  CHANGE_STATUS = "status"
  SWITCH_PRIORITY = "is_priority"
  TOGGLE_ARCHIVED = "is_archived"
  ASSIGN_JOB = "job"
  
@strawberry.enum
class ProductionOrderJobEnum(enum.Enum):
  MIX = "mix"
  REPAT = "repat"
 
@strawberry.enum
class ProductionOrderMixJobStatusEnum(enum.Enum):
  CANCELLED = "cancelled"
  COMPLETED = "completed"
  IN_PROGRESS = "in_progress"
  MIXED = "mixed"
  REASSIGNED = "reassigned"
 
@strawberry.enum
class ProductionOrderRepatJobStatusEnum(enum.Enum):
  CANCELLED = "cancelled"
  COMPLETED = "completed"
  IN_PROGRESS = "in_progress"
  REASSIGNED = "reassigned" 