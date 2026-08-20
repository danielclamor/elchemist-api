from __future__ import annotations

from typing import Annotated

import strawberry
from strawberry import relay

import models
from api_graphql.types.enums import ChillType, NicType
from api_graphql.types.feedback import Feedback


@strawberry.type
class FormulaType(relay.Node):
  slug: relay.NodeID[str]
  name: str
  brand: str
  chill_type: ChillType
  nic_type: NicType

  _model: strawberry.Private[models.Formula]

  @classmethod
  def from_model(cls, f: models.Formula) -> "FormulaType":
    return cls(
      slug=f.slug,
      name=f.name,
      brand=f.brand,
      chill_type=ChillType[f.chill_type.name],
      nic_type=NicType[f.nic_type.name],
      _model=f,
    )

  @strawberry.field
  def nic_profiles(self) -> list[Annotated["NicProfileType", strawberry.lazy("api_graphql.types.nic_profile")]]:
    from api_graphql.types.nic_profile import NicProfileType
    return [NicProfileType.from_model(p) for p in self._model.nic_profiles]

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