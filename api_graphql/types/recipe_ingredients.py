from __future__ import annotations

from typing import Optional

from graphql import GraphQLError
import strawberry

@strawberry.type
class RecipeIngredientType:
  name: str
  ratio: float
  volume_ml: float
  weight_g: float

@strawberry.input
class RecipeIngredientsInput:
  batch_volume_ml: float
  overrides: Optional[RecipeIngredientsOverrideInput] = strawberry.UNSET

@strawberry.input
class RecipeIngredientsOverrideInput:
  target_nic_str: Optional[float] = strawberry.UNSET
  target_pg: Optional[float] = strawberry.UNSET
  target_vg: Optional[float] = strawberry.UNSET
  flavorings: Optional[list[RecipeIngredientsFlavoringsOverrideInput]] = strawberry.UNSET
  nic_bases: Optional[list[RecipeIngredientsNicBasesOverrideInput]] = strawberry.UNSET

  def __post_init__(self):
    if any(v is None for v in vars(self).values()):
      raise GraphQLError(
        "Override fields cannot be null.",
        extensions={"code": "INPUT_ERROR", "inputObjectType": self.__strawberry_definition__.name}
      )

@strawberry.input
class RecipeIngredientsFlavoringsOverrideInput:
  name: str
  is_vg: bool
  ratio: float
  
@strawberry.input
class RecipeIngredientsNicBasesOverrideInput:
  code: str
  name: str
  is_vg: bool
  ratio: float

@strawberry.type
class RecipeIngredientGroup:
  ingredients: list[RecipeIngredientType]
  total_pg_ratio: float
  total_vg_ratio: float