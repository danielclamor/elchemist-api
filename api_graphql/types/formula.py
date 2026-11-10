from __future__ import annotations

from datetime import datetime
from typing import Annotated, TYPE_CHECKING, Optional

from graphql import GraphQLError
import strawberry
from strawberry import relay

from models import (
  Formula, 
  Flavoring, 
  NicBase
)

from api_graphql.types.enums import (
  ChillTypeEnum,
  NicTypeEnum,
)

from api_graphql.types.feedback import Feedback
from api_graphql.types.flavoring_option import FlavoringOptionIdentifierInput
from api_graphql.types.nic_base_option import NicBaseOptionIdentifierInput

if TYPE_CHECKING:
  from api_graphql.types.flavoring_option import FlavoringOptionType
  from api_graphql.types.nic_base_option import NicBaseOptionType

@strawberry.type
class FormulaType(relay.Node):
  id: relay.NodeID[str]
  slug: str
  name: str
  nic_level: float
  brand: str
  chill_type: ChillTypeEnum
  nic_type: NicTypeEnum
  is_pre_mix: bool
  is_old_mix: bool
  target_nic_str: float
  target_vg: float
  target_pg: float
  nic_base_nic_str: float
  created_at: datetime
  updated_at: datetime

  _model: strawberry.Private[Formula]

  @classmethod
  def from_model(cls, f: Formula) -> "FormulaType":
    return cls(
      id=f.id,
      slug=f.slug,
      name=f.name,
      nic_level= f.nic_level,
      brand=f.brand,
      chill_type=ChillTypeEnum[f.chill_type.name],
      nic_type=NicTypeEnum[f.nic_type.name],
      is_pre_mix=f.is_pre_mix,
      is_old_mix=f.is_old_mix,
      target_nic_str=f.target_nic_str,
      target_vg=f.target_vg,
      target_pg=f.target_pg,
      nic_base_nic_str=f.nic_base_nic_str,
      created_at=f.created_at,
      updated_at=f.updated_at,
      _model=f,
    )
    
  @strawberry.field
  def flavorings(self) -> list["FormulaFlavoringType"]:
    return [FormulaFlavoringType.from_model(b) for b in self._model.flavorings]
  
  @strawberry.field
  def nic_bases(self) -> list["FormulaNicBaseType"]:
    return [FormulaNicBaseType.from_model(b) for b in self._model.nic_bases]
  
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
class FormulaIdentifier:
  slug: str

@strawberry.input
class FormulaAddFlavoringInput:
  flavoring_option_name: str
  flavoring_option_is_vg: bool | None = None
  ratio: float

@strawberry.type
class FormulaAddFlavoringPayload:
  formula: FormulaType | None
  feedback: Feedback

@strawberry.input
class FormulaAddNicBaseInput:
  nic_base_option_code: str
  nic_base_option_name: str | None = None
  nic_base_option_is_vg: bool | None = None
  ratio: float

@strawberry.type
class FormulaAddNicBasePayload:
  formula: FormulaType | None
  feedback: Feedback

@strawberry.input
class FormulaCreateInput:
  name: str
  nic_level: float
  brand: str
  chill_type: ChillTypeEnum
  nic_type: NicTypeEnum
  nic_base_nic_str: float
  is_pre_mix: bool
  is_old_mix: bool
  target_nic_str: float
  target_vg: float
  target_pg: float
  
  def __post_init__(self):
    if sum([self.target_pg, self.target_vg]) != 1:
      raise GraphQLError(
        "sum of targetPg and targetVg must be 1",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )

@strawberry.type
class FormulaCreatePayload:
  formula: FormulaType | None
  feedback: Feedback

@strawberry.type
class FormulaDeletePayload:
  deleted_slug: str | None
  deleted_full_name: str | None
  feedback: Feedback

@strawberry.input
class FormulaUpdateInput:
  slug: Optional[str] = strawberry.UNSET
  name: Optional[str] = strawberry.UNSET
  nic_base_nic_str: Optional[float] = strawberry.UNSET
  is_old_mix: Optional[bool] = strawberry.UNSET
  target_nic_str: Optional[float] = strawberry.UNSET
  target_vg: Optional[float] = strawberry.UNSET
  target_pg: Optional[float] = strawberry.UNSET

@strawberry.type
class FormulaUpdatePayload:
  formula: FormulaType | None
  feedback: Feedback
  
@strawberry.type
class FormulaFlavoringType(relay.Node):
  id: relay.NodeID[str]
  ratio: float

  _model: strawberry.Private[Flavoring]

  @classmethod
  def from_model(cls, f: Flavoring) -> "FormulaFlavoringType":
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
class FormulaFlavoringIdentifierInput:
  id: relay.GlobalID
  
  @property
  def query_condition(self):
    return Flavoring.id == self.id.node_id

@strawberry.input
class FormulaFlavoringInput:
  flavoring_option_identifier: FlavoringOptionIdentifierInput
  ratio: float

@strawberry.type
class FormulaFlavoringAddPayload:
  formula_flavoring: FormulaFlavoringType | None
  feedback: Feedback

@strawberry.type
class FormulaFlavoringsBulkAddPayload:
  formula_flavorings: list[FormulaFlavoringAddPayload]
  feedback: Feedback
  
@strawberry.type
class FormulaFlavoringRemovePayload:
  removed_slug: str | None
  removed_name: str | None
  removed_ratio: float | None
  feedback: Feedback

@strawberry.type
class FormulaFlavoringsBulkRemovePayload:
  formula_flavorings: list[FormulaFlavoringRemovePayload]
  feedback: Feedback
  
@strawberry.type
class FormulaNicBaseType(relay.Node):
  id: relay.NodeID[str]
  ratio: float

  _model: strawberry.Private[NicBase]

  @classmethod
  def from_model(cls, b: NicBase) -> "FormulaNicBaseType":
    return cls(
      id=b.id,
      ratio=b.ratio,
      _model=b,
    )

  @strawberry.field
  def nic_base_option(self) -> Annotated["NicBaseOptionType", strawberry.lazy("api_graphql.types.nic_base_option")]:
    from api_graphql.types.nic_base_option import NicBaseOptionType
    return NicBaseOptionType.from_model(self._model.nic_base_option)

@strawberry.input
class FormulaNicBaseIdentifierInput:
  id: relay.GlobalID
  
  @property
  def query_condition(self):
    return NicBase.id == self.id.node_id
  
@strawberry.input
class FormulaNicBaseInput:
  nic_base_option_identifier: NicBaseOptionIdentifierInput
  ratio: float

@strawberry.type
class FormulaNicBasesSetPayload:
  formula_nic_bases: list[FormulaNicBaseType] | None
  feedback: Feedback

@strawberry.type
class FormulaNicBaseAddPayload:
  formula_nic_base: FormulaNicBaseType | None
  feedback: Feedback
  
@strawberry.type
class FormulaNicBasesBulkAddPayload:
  formula_nic_bases: list[FormulaNicBaseAddPayload]
  feedback: Feedback
  
@strawberry.type
class FormulaNicBaseRemovePayload:
  removed_code: str | None
  removed_name: str | None
  removed_ratio: float | None
  feedback: Feedback
  
@strawberry.type
class FormulaNicBasesBulkRemovePayload:
  formula_nic_bases: list[FormulaNicBaseRemovePayload]
  feedback: Feedback