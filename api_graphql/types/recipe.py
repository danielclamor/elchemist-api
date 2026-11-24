from __future__ import annotations

from typing import Optional

from graphql import GraphQLError
import strawberry

@strawberry.type
class MixParametersType:
  batch_volume_ml: float
  target_nic_str: float
  target_pg: float
  target_vg: float
  nic_base_nic_str: float
  flavorings: list[MixParametersFlavoringType]
  nic_bases: list[MixParametersNicBaseType]
  
  @classmethod
  def from_dict(cls, d: dict) -> "MixParametersType":
    return cls(
      batch_volume_ml=d["batch_volume_ml"],
      target_nic_str=d["target_nic_str"],
      target_vg=d["target_vg"],
      target_pg=d["target_pg"],
      nic_base_nic_str=d["nic_base_nic_str"],
      flavorings=[MixParametersFlavoringType(**f) for f in d["flavorings"]],
      nic_bases=[MixParametersNicBaseType(**b) for b in d["nic_bases"]],
    )
  
  @strawberry.field
  def nic_base_vg(self) -> float:
    return sum(n.ratio for n in self.nic_bases if n.is_vg)
  
  @strawberry.field
  def nic_base_pg(self) -> float:
    return sum(n.ratio for n in self.nic_bases if not n.is_vg)
  
@strawberry.type
class MixParametersFlavoringType:
  id: str
  slug: Optional[str] = None
  name: str
  is_vg: bool
  ratio: float
  
@strawberry.type
class MixParametersNicBaseType:
  id: str
  code: Optional[str] = None
  name: str
  is_vg: bool
  ratio: float

@strawberry.type
class RecipeType:
  mix_parameters: MixParametersType
  ingredients: list[RecipeIngredientType]
  total_ratio: float
  total_volume_ml: float
  total_weight_g: float
  
  @classmethod
  def from_snapshot(cls, r: dict) -> "RecipeType":
    return cls(
      mix_parameters=MixParametersType.from_dict(r["mix_parameters"]),
      ingredients=[RecipeIngredientType(**i) for i in r["ingredients"]],
      total_ratio=r["total_ratio"],
      total_volume_ml=r["total_volume_ml"],
      total_weight_g=r["total_weight_g"],
    )

@strawberry.input
class RecipeInput:
  batch_volume_ml: float
  overrides: Optional[RecipeIngredientsOverrideInput] = strawberry.UNSET

@strawberry.input
class RecipeDiyInput:
  batch_volume_ml: float
  target_nic_str: float
  target_pg: float
  target_vg: float
  nic_base_nic_str: float
  flavorings: list[RecipeIngredientsFlavoringInput]
  nic_base_vg: float
  nic_base_pg: float
  
  def __post_init__(self):
    if sum([self.target_pg, self.target_vg]) != 1:
      raise GraphQLError(
        "sum of targetPg and targetVg must be 1",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )
      
    if sum([self.nic_base_pg, self.nic_base_vg]) != 1:
      raise GraphQLError(
        "sum of nicBasePg and nicBaseVg must be 1",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )

@strawberry.type
class RecipeIngredientType:
  name: str
  ratio: float
  volume_ml: float
  weight_g: float

@strawberry.input
class RecipeIngredientsOverrideInput:
  target_nic_str: Optional[float] = strawberry.UNSET
  target_pg: Optional[float] = strawberry.UNSET
  target_vg: Optional[float] = strawberry.UNSET
  flavorings: Optional[list[RecipeIngredientsFlavoringInput]] = strawberry.UNSET
  nic_bases: Optional[list[RecipeIngredientsNicBaseInput]] = strawberry.UNSET

  def __post_init__(self):
    if any(v is None for v in vars(self).values()):
      raise GraphQLError(
        "Override fields cannot be null.",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )

    target_pg_provided = self.target_pg is not strawberry.UNSET
    target_vg_provided = self.target_vg is not strawberry.UNSET    
    
    if target_pg_provided != target_vg_provided:
      raise GraphQLError(
        "targetPg and targetVg must be provided together",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )
    
    if sum([self.target_pg, self.target_vg]) != 1:
      raise GraphQLError(
        "sum of targetPg and targetVg must be 1",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )
      
    if self.nic_bases is not strawberry.UNSET:
      total_nic_base_ratio = sum(b.ratio for b in self.nic_bases)
      if total_nic_base_ratio != 1:
        raise GraphQLError(
          "sum of nicBases must be 1",
          extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
        )
    
@strawberry.input
class RecipeIngredientsFlavoringInput:
  slug: Optional[str] = strawberry.UNSET
  name: str
  is_vg: bool
  ratio: float
  
@strawberry.input
class RecipeIngredientsNicBaseInput:
  code: Optional[str] = strawberry.UNSET
  name: str
  is_vg: bool
  ratio: float

@strawberry.type
class RecipeIngredientGroup:
  ingredients: list[RecipeIngredientType]
  total_pg_ratio: float
  total_vg_ratio: float