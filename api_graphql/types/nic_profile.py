from __future__ import annotations

from typing import Annotated, TYPE_CHECKING, Optional

from graphql import GraphQLError
import strawberry
from strawberry import relay

from models import (
  NicProfile, 
  Flavoring, 
  NicBase
)

from api_graphql.types.feedback import Feedback
from api_graphql.types.flavoring_option import FlavoringOptionIdentifierInput
from api_graphql.types.nic_base_option import NicBaseOptionIdentifierInput

if TYPE_CHECKING:
  from api_graphql.types.formula import FormulaType
  from api_graphql.types.flavoring_option import FlavoringOptionType
  from api_graphql.types.nic_base_option import NicBaseOptionType

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

  _model: strawberry.Private[NicProfile]

  @classmethod
  def from_model(cls, p: NicProfile) -> "NicProfileType":
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

  @relay.connection(relay.ListConnection["NicProfileFlavoringType"])
  def flavorings(self) -> list["NicProfileFlavoringType"]:
    return [NicProfileFlavoringType.from_model(b) for b in self._model.flavorings]

  @relay.connection(relay.ListConnection["NicProfileNicBaseType"])
  def nic_bases(self) -> list["NicProfileNicBaseType"]:
    return [NicProfileNicBaseType.from_model(b) for b in self._model.nic_bases]

@strawberry.input
class NicProfileIdentifierInput:
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
      expected_name = NicProfileType.__strawberry_definition__.name
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
      return NicProfile.id == value.node_id
    else:
      return getattr(NicProfile, attr) == value

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
  slug: Optional[str] = strawberry.UNSET
  name: Optional[str] = strawberry.UNSET
  nic_base_nic_str: Optional[float] = strawberry.UNSET
  is_old_mix: Optional[bool] = strawberry.UNSET
  target_nic_str: Optional[float] = strawberry.UNSET
  target_vg: Optional[float] = strawberry.UNSET
  target_pg: Optional[float] = strawberry.UNSET

@strawberry.type
class NicProfileUpdatePayload:
  nic_profile: NicProfileType | None
  feedback: Feedback
  
@strawberry.type
class NicProfileFlavoringType(relay.Node):
  id: relay.NodeID[str]
  ratio: float

  _model: strawberry.Private[Flavoring]

  @classmethod
  def from_model(cls, f: Flavoring) -> "NicProfileFlavoringType":
    return cls(
      id=f.id,
      ratio=f.ratio,
      _model=f,
    )

  @strawberry.field
  def flavoring_option(self) -> Annotated["FlavoringOptionType", strawberry.lazy("api_graphql.types.flavoring_option")]:
    from api_graphql.types.flavoring_option import FlavoringOptionType
    return FlavoringOptionType.from_model(self._model.flavoring_option)

@strawberry.input
class NicProfileFlavoringIdentifierInput:
  id: relay.GlobalID
  
  @property
  def query_condition(self):
    return Flavoring.id == self.id.node_id

@strawberry.input
class NicProfileFlavoringInput:
  flavoring_option_identifier: FlavoringOptionIdentifierInput
  ratio: float

@strawberry.type
class NicProfileFlavoringAddPayload:
  nic_profile_flavoring: NicProfileFlavoringType | None
  feedback: Feedback

@strawberry.type
class NicProfileFlavoringsBulkAddPayload:
  nic_profile_flavorings: list[NicProfileFlavoringAddPayload]
  feedback: Feedback
  
@strawberry.type
class NicProfileFlavoringRemovePayload:
  removed_slug: str | None
  removed_name: str | None
  removed_ratio: float | None
  feedback: Feedback

@strawberry.type
class NicProfileFlavoringsBulkRemovePayload:
  nic_profile_flavorings: list[NicProfileFlavoringRemovePayload]
  feedback: Feedback
  
@strawberry.type
class NicProfileNicBaseType:
  id: relay.NodeID[str]
  ratio: float

  _model: strawberry.Private[NicBase]

  @classmethod
  def from_model(cls, f: NicBase) -> "NicProfileNicBaseType":
    return cls(
      ratio=f.ratio,
      _model=f,
    )

  @strawberry.field
  def nic_base_option(self) -> Annotated["NicBaseOptionType", strawberry.lazy("api_graphql.types.nic_base_option")]:
    from api_graphql.types.nic_base_option import NicBaseOptionType
    return NicBaseOptionType.from_model(self._model.nic_base_option)

@strawberry.input
class NicProfileNicBaseIdentifierInput:
  id: relay.GlobalID
  
  @property
  def query_condition(self):
    return NicBase.id == self.id.node_id
  
@strawberry.input
class NicProfileNicBaseInput:
  nic_base_option_identifier: NicBaseOptionIdentifierInput
  ratio: float

@strawberry.input
class NicProfileNicBaseAddPayload:
  nic_profile_nic_base: NicProfileNicBaseType | None
  feedback: Feedback
  
@strawberry.type
class NicProfileNicBasesBulkAddPayload:
  nic_profile_nic_bases: list[NicProfileNicBaseAddPayload]
  feedback: Feedback
  
@strawberry.type
class NicProfileNicBaseRemovePayload:
  removed_code: str | None
  removed_name: str | None
  removed_ratio: float | None
  feedback: Feedback
  
@strawberry.type
class NicProfileNicBasesBulkRemovePayload:
  nic_profile_nic_bases: list[NicProfileNicBaseRemovePayload]
  feedback: Feedback