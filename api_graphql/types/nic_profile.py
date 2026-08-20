from typing import List

import strawberry
from strawberry import relay

from api_graphql.types.feedback import Feedback
from api_graphql.types.flavoring import FlavoringType
from api_graphql.types.nic_base import NicBaseType

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