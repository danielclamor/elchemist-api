from __future__ import annotations
from typing import Optional

from graphql import GraphQLError
import strawberry
from strawberry import relay

import models
from api_graphql.types.feedback import Feedback


@strawberry.type
class FlavoringOptionType(relay.Node):
  id: relay.NodeID[str]
  slug: str
  name: str
  is_vg: bool

  @classmethod
  def from_model(cls, o: models.FlavoringOption) -> "FlavoringOptionType":
    return cls(
      id=o.id,
      slug=o.slug,
      name=o.name,
      is_vg=o.is_vg
    )

@strawberry.input
class FlavoringOptionIdentifierInput:
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
      expected_name = FlavoringOptionType.__strawberry_definition__.name
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
      return models.FlavoringOption.id == value.node_id
    else:
      return getattr(models.FlavoringOption, attr) == value

@strawberry.input
class FlavoringOptionCreateInput:
  name: str
  is_vg: bool

@strawberry.input
class FlavoringOptionBulkCreateInput:
  flavoring_options: list[FlavoringOptionCreateInput]

@strawberry.type
class FlavoringOptionCreatePayload:
  flavoring_option: FlavoringOptionType | None
  feedback: Feedback
  
@strawberry.type
class FlavoringOptionBulkCreatePayload:
  flavoring_options: list[FlavoringOptionCreatePayload]
  feedback: Feedback