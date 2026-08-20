from datetime import datetime
import enum

import strawberry
from strawberry import relay
from typing import List

@strawberry.type
class BrandEdge:
  cursor: str
  node: str

@strawberry.type
class BrandConnection:
  edges: List[BrandEdge]
  page_info: relay.PageInfo

@strawberry.type
class NicBaseOptionType(relay.Node):
  code: relay.NodeID[str]
  name: str
  is_vg: bool

@strawberry.type
class NicBaseType:
  ratio: float
  nic_base_option: NicBaseOptionType

@strawberry.type
class FlavoringOptionType(relay.Node):
  slug: relay.NodeID[str]
  name: str
  is_vg: bool

@strawberry.type
class FlavoringType:
  flavoring_option: FlavoringOptionType
  ratio: float
  
@strawberry.type
class NicProfileType(relay.Node):
  slug: relay.NodeID[str]
  name: str
  full_name: str
  is_pre_mix: bool
  is_old_mix: bool
  target_nic_str: float
  target_vg: float
  target_pg: float
  nic_base_nic_str: float
  nic_bases: List[NicBaseType]
  flavorings: List[FlavoringType]

@strawberry.enum
class BottleColor(enum.Enum):
  BLACK = "black"
  CLEAR = "clear"
  WHITE = "white"

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

@strawberry.type
class EliquidType(relay.Node):
  upc: relay.NodeID[str]
  description: str
  brand: str
  chill_type: ChillType
  nic_type: NicType
  size: SizeOption
  nic_level: NicLevelOption
  bottle_color: BottleColor
  nic_profile: NicProfileType | None = None

@strawberry.type
class FormulaType(relay.Node):
  slug: relay.NodeID[str]
  name: str
  brand: str
  chill_type: ChillType
  nic_type: NicType
  nic_profiles: List[NicProfileType]
  
@strawberry.enum
class FeedbackStatus(enum.Enum):
  SUCCESS = "success"
  FAILED = "failed"
  CANCELLED = "cancelled"
  
@strawberry.type
class Feedback:
  status: FeedbackStatus
  message: str | None = None
     
@strawberry.input
class FlavoringOptionCreateInput:
  name: str
  is_vg: bool
  
@strawberry.type
class FlavoringOptionCreatePayload:
  flavoring_option: FlavoringOptionType | None
  feedback: Feedback
     
@strawberry.input
class FormulaCreateInput:
  name: str
  brand: str
  chill_type: ChillType
  nic_type: NicType
  
@strawberry.type
class FormulaCreatePayload:
  formula: FormulaType
  feedback: Feedback

@strawberry.input
class FormulaDeleteInput:
  slug: str

@strawberry.type
class FormulaDeletePayload:
  deleted_slug: str | None
  deleted_name: str | None
  feedback: Feedback
  
@strawberry.input
class FormulaUpdateIdentifier:
  slug: str

@strawberry.input
class FormulaUpdateInput:
  slug: str | None = None
  name: str | None = None
  brand: str | None = None
  chill_type: ChillType | None = None
  nic_type: NicType | None = None

@strawberry.type
class FormulaUpdatePayload:
  formula: FormulaType | None
  feedback: Feedback
  
@strawberry.input
class NicBaseOptionCreateInput:
  code: str
  name: str
  is_vg: bool
  
@strawberry.type
class NicBaseOptionCreatePayload:
  nic_base_option: NicBaseOptionType | None
  feedback: Feedback

@strawberry.input
class NicProfileAddFlavoringInput:
  flavoring_option_name: str
  flavoring_option_is_vg: bool | None = None
  ratio: float

@strawberry.type
class NicProfileAddFlavoringPayload:
  nic_profile: NicProfileType | None
  feedback: Feedback

@strawberry.input
class NicProfileAddNicBaseInput:
  nic_base_option_code: str
  nic_base_option_name: str | None = None
  nic_base_option_is_vg: bool | None = None
  ratio: float

@strawberry.type
class NicProfileAddNicBasePayload:
  nic_profile: NicProfileType | None
  feedback: Feedback

@strawberry.input
class NicProfileCreateInput:
  name: str
  nic_base_nic_str: float
  is_old_mix: bool
  target_nic_str: float
  target_vg: float
  target_pg: float

@strawberry.type
class NicProfileCreatePayload:
  nic_profile: NicProfileType | None
  feedback: Feedback
  
@strawberry.input
class NicProfileDeleteInput:
  slug: str
  
@strawberry.type
class NicProfileDeletePayload:
  deleted_slug: str | None
  deleted_full_name: str | None
  feedback: Feedback

@strawberry.input
class NicProfileUpdateIdentifier:
  slug: str

@strawberry.input
class NicProfileUpdateInput:
  slug: str | None = None
  name: str | None = None
  nic_base_nic_str: float | None = None
  is_old_mix: bool | None = None
  target_nic_str: float | None = None
  target_vg: float | None = None
  target_pg: float | None = None
  
@strawberry.type
class NicProfileUpdatePayload:
  nic_profile: NicProfileType | None
  feedback: Feedback
  
@strawberry.enum
class ProductionOrderStatus(enum.Enum):
  CANCELLED = "cancelled"
  DELIVERED = "delivered"
  MIXED = "mixed"
  PENDING = "pending"

@strawberry.type
class ProductionOrderType(relay.Node):
  order_numer: str
  eliquid: EliquidType
  quantity: int
  status: ProductionOrderStatus
  is_priority: bool
  created_at: datetime