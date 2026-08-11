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
class FlavoringType:
    name: str
    ratio: float
    is_vg: bool

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

@strawberry.type
class FormulaType:
    slug: str
    name: str
    brand: str
    chill_type: str
    nic_type: str
    nic_profiles: List[NicProfileType]