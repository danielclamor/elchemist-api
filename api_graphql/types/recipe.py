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

@strawberry.input
class RecipeInput:
  batch_volume_ml: float
  overrides: Optional[RecipeIngredientsOverrideInput] = strawberry.UNSET

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
  flavorings: Optional[list[RecipeIngredientsFlavoringOverrideInput]] = strawberry.UNSET
  nic_bases: Optional[list[RecipeIngredientsNicBaseOverrideInput]] = strawberry.UNSET

  def __post_init__(self):
    if any(v is None for v in vars(self).values()):
      raise GraphQLError(
        "Override fields cannot be null.",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )

@strawberry.input
class RecipeIngredientsFlavoringOverrideInput:
  name: str
  is_vg: bool
  ratio: float
  
@strawberry.input
class RecipeIngredientsNicBaseOverrideInput:
  code: str
  name: str
  is_vg: bool
  ratio: float

@strawberry.type
class RecipeIngredientGroup:
  ingredients: list[RecipeIngredientType]
  total_pg_ratio: float
  total_vg_ratio: float