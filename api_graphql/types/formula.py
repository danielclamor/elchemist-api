from typing import List

import strawberry
from strawberry import relay

from api_graphql.types.enums import ChillType, NicType
from api_graphql.types.feedback import Feedback
from api_graphql.types.nic_profile import NicProfileType

@strawberry.type
class FormulaType(relay.Node):
  id: relay.NodeID[str]
  slug: str
  name: str
  brand: str
  chill_type: ChillType
  nic_type: NicType
  nic_profiles: List[NicProfileType]
  
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