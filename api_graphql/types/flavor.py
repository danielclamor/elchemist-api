from __future__ import annotations

from datetime import datetime
from typing import Optional

from graphql import GraphQLError
import strawberry
from strawberry import relay

from api_graphql.types.enums import ChillTypeEnum, NicTypeEnum
from models import Flavor


@strawberry.type
class FlavorType(relay.Node):
  id: relay.NodeID[str]
  slug: str
  name: str
  brand: str
  chill_type: ChillTypeEnum
  nic_type: NicTypeEnum
  created_at: datetime
  updated_at: datetime

  _model: strawberry.Private[Flavor]

  @classmethod
  def from_model(cls, f: Flavor) -> "FlavorType":
    return cls(
      id=f.id,
      slug=f.slug,
      name=f.name,
      brand=f.brand,
      chill_type=ChillTypeEnum[f.chill_type.name],
      nic_type=NicTypeEnum[f.nic_type.name],
      created_at=f.created_at,
      updated_at=f.updated_at,
      _model=f,
    )
    
@strawberry.input
class FlavorIdentifierInput:
  id: Optional[relay.GlobalID] = strawberry.UNSET
  slug: Optional[str] = strawberry.UNSET
  
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
      expected_name = FlavorType.__strawberry_definition__.name
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
      return Flavor.id == value.node_id
    else:
      return getattr(Flavor, attr) == value