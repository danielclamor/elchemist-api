from __future__ import annotations

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
class FlavoringOptionCreateInput:
  name: str
  is_vg: bool

@strawberry.type
class FlavoringOptionCreatePayload:
  flavoring_option: FlavoringOptionType | None
  feedback: Feedback

@strawberry.type
class FlavoringType:
  ratio: float

  _model: strawberry.Private[models.Flavoring]

  @classmethod
  def from_model(cls, f: models.Flavoring) -> "FlavoringType":
    return cls(
      ratio=f.ratio,
      _model=f,
    )

  @strawberry.field
  def flavoring_option(self) -> "FlavoringOptionType":
    return FlavoringOptionType.from_model(self._model.flavoring_option)