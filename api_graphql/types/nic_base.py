from __future__ import annotations
from typing import Optional

from graphql import GraphQLError
import strawberry
from strawberry import relay

from models import NicBase, NicBaseOption
from api_graphql.types.feedback import Feedback


@strawberry.type
class NicBaseOptionType(relay.Node):
  id: relay.NodeID[str]
  code: str
  name: str
  is_vg: bool

  @classmethod
  def from_model(cls, o: NicBaseOption) -> "NicBaseOptionType":
    return cls(
      id=o.id,
      code=o.code,
      name=o.name,
      is_vg=o.is_vg
    )
    
@strawberry.input
class NicBaseOptionIdentifierInput:
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
      expected_name = NicBaseOptionType.__strawberry_definition__.name
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
      return NicBaseOption.id == value.node_id
    else:
      return getattr(NicBaseOption, attr) == value

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

  _model: strawberry.Private[NicBase]

  @classmethod
  def from_model(cls, f: NicBase) -> "NicBaseType":
    return cls(
      ratio=f.ratio,
      _model=f,
    )

  @strawberry.field
  def nic_base_option(self) -> "NicBaseOptionType":
    return NicBaseOptionType.from_model(self._model.nic_base_option)