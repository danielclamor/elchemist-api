from __future__ import annotations

from typing import Annotated, TYPE_CHECKING

import strawberry
from strawberry import relay

import models
from api_graphql.types.feedback import Feedback

if TYPE_CHECKING:
  from api_graphql.types.formula import FormulaType
  from api_graphql.types.flavoring import FlavoringType
  from api_graphql.types.nic_base import NicBaseType

@strawberry.type
class NicProfileType(relay.Node):
  id: relay.NodeID[str]
  slug: str
  name: str
  is_pre_mix: bool
  is_old_mix: bool
  target_nic_str: float
  target_vg: float
  target_pg: float
  nic_base_nic_str: float

  _model: strawberry.Private[models.NicProfile]

  @classmethod
  def from_model(cls, p: models.NicProfile) -> "NicProfileType":
    return cls(
      id=p.id,
      slug=p.slug,
      name=p.name,
      is_pre_mix=p.is_pre_mix,
      is_old_mix=p.is_old_mix,
      target_nic_str=p.target_nic_str,
      target_vg=p.target_vg,
      target_pg=p.target_pg,
      nic_base_nic_str=p.nic_base_nic_str,
      _model=p,
    )
    
  @strawberry.field
  def full_name(self) -> str:
    return self._model.full_name
    
  @strawberry.field
  def formula(self) -> Annotated["FormulaType", strawberry.lazy("api_graphql.types.formula")]:
    from api_graphql.types.formula import FormulaType
    return FormulaType.from_model(self._model.formula)

  @relay.connection(relay.ListConnection[Annotated["NicBaseType", strawberry.lazy("api_graphql.types.nic_base")]])
  def nic_bases(self) -> list[Annotated["NicBaseType", strawberry.lazy("api_graphql.types.nic_base")]]:
    from api_graphql.types.nic_base import NicBaseType
    return [NicBaseType.from_model(b) for b in self._model.nic_bases]

  @relay.connection(relay.ListConnection[Annotated["FlavoringType", strawberry.lazy("api_graphql.types.flavoring")]])
  def flavorings(self) -> list[Annotated["FlavoringType", strawberry.lazy("api_graphql.types.flavoring")]]:
    from api_graphql.types.flavoring import FlavoringType
    return [FlavoringType.from_model(b) for b in self._model.flavorings]

@strawberry.input
class NicProfileIdentifier:
  slug: str

@strawberry.input
class NicProfileAddFlavoringInput:
  flavoring_option_name: str
  flavoring_option_is_vg: bool | None = None
  ratio: float

@strawberry.type
class NicProfileAddFlavoringPayload:
  nic_profile: NicProfileType | None
  feedback: Feedback

@strawberry.input
class NicProfileAddNicBaseInput:
  nic_base_option_code: str
  nic_base_option_name: str | None = None
  nic_base_option_is_vg: bool | None = None
  ratio: float

@strawberry.type
class NicProfileAddNicBasePayload:
  nic_profile: NicProfileType | None
  feedback: Feedback

@strawberry.input
class NicProfileCreateInput:
  name: str
  nic_base_nic_str: float
  is_old_mix: bool
  target_nic_str: float
  target_vg: float
  target_pg: float

@strawberry.type
class NicProfileCreatePayload:
  nic_profile: NicProfileType | None
  feedback: Feedback

@strawberry.type
class NicProfileDeletePayload:
  deleted_slug: str | None
  deleted_full_name: str | None
  feedback: Feedback

@strawberry.input
class NicProfileUpdateInput:
  slug: str | None = None
  name: str | None = None
  nic_base_nic_str: float | None = None
  is_old_mix: bool | None = None
  target_nic_str: float | None = None
  target_vg: float | None = None
  target_pg: float | None = None

@strawberry.type
class NicProfileUpdatePayload:
  nic_profile: NicProfileType | None
  feedback: Feedback