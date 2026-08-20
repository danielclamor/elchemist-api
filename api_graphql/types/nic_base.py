import strawberry
from strawberry import relay

from api_graphql.types.feedback import Feedback

@strawberry.type
class NicBaseOptionType(relay.Node):
  code: relay.NodeID[str]
  name: str
  is_vg: bool

@strawberry.input
class NicBaseOptionCreateInput:
  code: str
  name: str
  is_vg: bool
  
@strawberry.type
class NicBaseOptionCreatePayload:
  nic_base_option: NicBaseOptionType | None
  feedback: Feedback

@strawberry.type
class NicBaseType:
  ratio: float
  nic_base_option: NicBaseOptionType
