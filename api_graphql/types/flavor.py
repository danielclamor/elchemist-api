from __future__ import annotations
from datetime import datetime

from graphql import GraphQLError

from typing import Annotated, TYPE_CHECKING, Optional

import strawberry
from strawberry import relay

from models import Flavor

from api_graphql.types.enums import ChillTypeEnum, NicTypeEnum
from api_graphql.types.feedback import Feedback

if TYPE_CHECKING:
  from api_graphql.types.formula import FormulaType
  from api_graphql.types.flavoring_option import FlavoringOptionType

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

  @relay.connection(relay.ListConnection[Annotated["FormulaType", strawberry.lazy("api_graphql.types.formula")]])
  def formulas(self) -> list[Annotated["FormulaType", strawberry.lazy("api_graphql.types.formula")]]:
    from api_graphql.types.formula import FormulaType
    return [FormulaType.from_model(p) for p in self._model.formulas]

  @relay.connection(relay.ListConnection[Annotated["FlavoringOptionType", strawberry.lazy("api_graphql.types.flavoring_option")]])
  def flavoring_options(self) -> list[Annotated["FlavoringOptionType", strawberry.lazy("api_graphql.types.flavoring_option")]]:
    from api_graphql.types.flavoring_option import FlavoringOptionType
    flavoring_options = []
    for p in self._model.formulas:
      flavoring_options = [f.flavoring_option for f in p.flavorings]
    
    return [FlavoringOptionType.from_model(o) for o in list(set(flavoring_options))]

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
  
@strawberry.input
class FlavorCreateInput:
  name: str
  brand: str
  chill_type: ChillTypeEnum
  nic_type: NicTypeEnum

@strawberry.type
class FlavorCreatePayload:
  flavor: FlavorType
  feedback: Feedback

@strawberry.type
class FlavorDeletePayload:
  deleted_slug: str | None
  deleted_name: str | None
  feedback: Feedback

@strawberry.input
class FlavorUpdateInput:
  slug: Optional[str] = strawberry.UNSET
  name: Optional[str] = strawberry.UNSET
  brand: Optional[str] = strawberry.UNSET
  chill_type: Optional[ChillTypeEnum] = strawberry.UNSET
  nic_type: Optional[NicTypeEnum] = strawberry.UNSET

@strawberry.type
class FlavorUpdatePayload:
  flavor: FlavorType | None
  feedback: Feedback