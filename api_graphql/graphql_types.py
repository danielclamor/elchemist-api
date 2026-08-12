import enum

import strawberry
from typing import List

@strawberry.type
class NicBaseOptionType:
  code: str
  name: str
  is_vg: bool

@strawberry.type
class NicBaseType:
  ratio: float
  nic_base_option: NicBaseOptionType

@strawberry.type
class FlavoringOptionType:
  slug: str
  name: str
  is_vg: bool

@strawberry.type
class FlavoringType:
  flavoring_option: FlavoringOptionType
  ratio: float
  
@strawberry.type
class NicProfileType:
  slug: str
  name: str
  full_name: str
  is_new_mix: bool
  target_nic_str: float
  target_vg: float
  target_pg: float
  nic_base_nic_str: float
  nic_bases: List[NicBaseType]
  flavorings: List[FlavoringType]

@strawberry.enum
class ChillType(enum.Enum):
    CHILLED = "CHILLED"
    NON_CHILLED = "NON_CHILLED"

@strawberry.enum
class NicType(enum.Enum):
    SALT = "salt"
    FREEBASE = "freebase"

@strawberry.type
class FormulaType:
    slug: str
    name: str
    brand: str
    chill_type: ChillType
    nic_type: NicType
    nic_profiles: List[NicProfileType]