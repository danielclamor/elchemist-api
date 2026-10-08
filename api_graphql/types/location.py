from datetime import datetime
from typing import Optional

from graphql import GraphQLError
import strawberry
from strawberry import relay

from models import Location

@strawberry.type
class LocationType(relay.Node):
  id: relay.NodeID[str]
  code: str
  name: str
  address: str
  city: str
  province: str
  is_hq: bool
  created_at: datetime
  updated_at: datetime
  
  @classmethod
  def from_model(cls, l: Location) -> "LocationType":
    return cls(
      id=l.id,
      code=l.code,
      name=l.name,
      address=l.address,
      city=l.city,
      province=l.province,
      is_hq=l.is_hq,
      created_at=l.created_at,
      updated_at=l.updated_at,
    )
    
@strawberry.input
class LocationIdentifierInput:
  id: Optional[relay.GlobalID] = strawberry.UNSET
  code: Optional[str] = strawberry.UNSET
  
  def __post_init__(self):
    if any(v is None for v in vars(self).values()):
      raise GraphQLError(
        "Identifier fields cannot be null.",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )
    
    provided = sum(1 for value in vars(self).values() if value is not strawberry.UNSET)
    if provided != 1:
      raise GraphQLError(
        "Exactly one identifier must be provided.",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )
    
    if self.id is not strawberry.UNSET:
      type_name = self.id.type_name
      expected_name = LocationType.__strawberry_definition__.name
      if type_name != expected_name:
        raise GraphQLError(
          f"Expected {expected_name} ID, got {type_name} ID",
          extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
        )
        
  @property
  def provided(self):
    return next((a, v) for a, v in vars(self).items() if v is not strawberry.UNSET)

  @property
  def query_condition(self):
    attr, value = self.provided
    
    if attr == "id":
      return Location.id == value.node_id
    else:
      return getattr(Location, attr) == value