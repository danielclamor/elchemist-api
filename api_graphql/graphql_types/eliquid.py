import strawberry
from strawberry import relay

from api_graphql.graphql_types.enums import ChillType, NicType, SizeOption, NicLevelOption, BottleColor
from api_graphql.graphql_types.nic_profile import NicProfileType

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