from __future__ import annotations

from graphql import GraphQLError

from typing import Annotated, TYPE_CHECKING, Optional

import strawberry
from strawberry import relay

import models
from api_graphql.types.enums import ChillType, NicType
from api_graphql.types.feedback import Feedback

if TYPE_CHECKING:
  from api_graphql.types.nic_profile import NicProfileType

@strawberry.type
class FormulaType(relay.Node):
  id: relay.NodeID[str]
  slug: str
  name: str
  brand: str
  chill_type: ChillType
  nic_type: NicType

  _model: strawberry.Private[models.Formula]

  @classmethod
  def from_model(cls, f: models.Formula) -> "FormulaType":
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