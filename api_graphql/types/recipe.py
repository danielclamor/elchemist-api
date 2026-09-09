from __future__ import annotations

from typing import Optional

from graphql import GraphQLError
import strawberry

from api_graphql.types.nic_profile import NicProfileType

@strawberry.type
class MixParametersType:
  batch_volume_ml: float
  target_nic_str: float
  target_pg: float
  target_vg: float
  nic_base_nic_str: float
  flavorings: list[MixParametersFlavorings]
  nic_bases: list[MixParametersNicBases]
  
@strawberry.type
class MixParametersFlavorings:
  name: str
  is_vg: bool
  ratio: float
  
@strawberry.type
class MixParametersNicBases:
  code: str
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
  nic_profile: NicProfileType

@strawberry.input
class RecipeInput:
  batch_volume_ml: float
  overrides: Optional[RecipeIngredientsOverrideInput] = strawberry.UNSET

@strawberry.type
class RecipeDiyType:
  mix_parameters: MixParametersType
  ingredients: list[RecipeIngredientType]
  total_ratio: float
  total_volume_ml: float
  total_weight_g: float

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
  name: str
  is_vg: bool
  ratio: float
  
@strawberry.input
class RecipeIngredientsNicBaseInput:
  code: str
  name: str
  is_vg: bool
  ratio: float

@strawberry.type
class RecipeIngredientGroup:
  ingredients: list[RecipeIngredientType]
  total_pg_ratio: float
  total_vg_ratio: float