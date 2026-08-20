import strawberry
from strawberry import relay

from api_graphql.types.feedback import Feedback

@strawberry.type
class FlavoringOptionType(relay.Node):
  id: relay.NodeID[str]
  slug: str
  name: str
  is_vg: bool
  
@strawberry.input
class FlavoringOptionCreateInput:
  name: str
  is_vg: bool
  
@strawberry.type
class FlavoringOptionCreatePayload:
  flavoring_option: FlavoringOptionType | None
  feedback: Feedback

@strawberry.type
class FlavoringType:
  flavoring_option: FlavoringOptionType
  ratio: float