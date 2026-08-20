from __future__ import annotations

import strawberry
from strawberry import relay

import models
from api_graphql.types.feedback import Feedback


@strawberry.type
class NicBaseOptionType(relay.Node):
  code: relay.NodeID[str]
  name: str
  is_vg: bool

  @classmethod
  def from_model(cls, o: models.NicBaseOption) -> "NicBaseOptionType":
    return cls(
      code=o.code,
      name=o.name,
      is_vg=o.is_vg
    )

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

  _model: strawberry.Private[models.NicBase]

  @classmethod
  def from_model(cls, f: models.NicBase) -> "NicBaseType":
    return cls(
      ratio=f.ratio,
      _model=f,
    )

  @strawberry.field
  def nic_base_option(self) -> "NicBaseOptionType":
    return NicBaseOptionType.from_model(self._model.nic_base_option)