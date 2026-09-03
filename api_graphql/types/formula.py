from __future__ import annotations

from graphql import GraphQLError

from typing import Annotated, TYPE_CHECKING, Optional

import strawberry
from strawberry import relay

from models import Formula, ChillType, NicType

from api_graphql.types.enums import ChillType, NicType
from api_graphql.types.feedback import Feedback

if TYPE_CHECKING:
  from api_graphql.types.nic_profile import NicProfileType
  from api_graphql.types.flavoring_option import FlavoringOptionType

@strawberry.type
class FormulaType(relay.Node):
  id: relay.NodeID[str]
  slug: str
  name: str
  brand: str
  chill_type: ChillType
  nic_type: NicType

  _model: strawberry.Private[Formula]

  @classmethod
  def from_model(cls, f: Formula) -> "FormulaType":
    return cls(
      id=f.id,
      slug=f.slug,
      name=f.name,
      brand=f.brand,
      chill_type=ChillType[f.chill_type.name],
      nic_type=NicType[f.nic_type.name],
      _model=f,
    )

  @relay.connection(relay.ListConnection[Annotated["NicProfileType", strawberry.lazy("api_graphql.types.nic_profile")]])
  def nic_profiles(self) -> list[Annotated["NicProfileType", strawberry.lazy("api_graphql.types.nic_profile")]]:
    from api_graphql.types.nic_profile import NicProfileType
    return [NicProfileType.from_model(p) for p in self._model.nic_profiles]

  @relay.connection(relay.ListConnection[Annotated["FlavoringOptionType", strawberry.lazy("api_graphql.types.flavoring_option")]])
  def flavoring_options(self) -> list[Annotated["FlavoringOptionType", strawberry.lazy("api_graphql.types.flavoring_option")]]:
    from api_graphql.types.flavoring_option import FlavoringOptionType
    flavoring_options = []
    for p in self._model.nic_profiles:
      flavoring_options = [f.flavoring_option for f in p.flavorings]
    
    return [FlavoringOptionType.from_model(o) for o in list(set(flavoring_options))]

@strawberry.input
class FormulaIdentifierInput:
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
      expected_name = FormulaType.__strawberry_definition__.name
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
      return Formula.id == value.node_id
    else:
      return getattr(Formula, attr) == value
  
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

@strawberry.type
class FormulaDeletePayload:
  deleted_slug: str | None
  deleted_name: str | None
  feedback: Feedback

@strawberry.input
class FormulaUpdateInput:
  slug: Optional[str] = strawberry.UNSET
  name: Optional[str] = strawberry.UNSET
  brand: Optional[str] = strawberry.UNSET
  chill_type: Optional[ChillType] = strawberry.UNSET
  nic_type: Optional[NicType] = strawberry.UNSET

@strawberry.type
class FormulaUpdatePayload:
  formula: FormulaType | None
  feedback: Feedback