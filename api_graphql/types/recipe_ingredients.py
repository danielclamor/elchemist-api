import strawberry

from api_graphql.types.nic_profile import NicProfileIdentifierInput

@strawberry.type
class RecipeIngredientType:
  name: str
  ratio: float
  volume_ml: float
  weight_g: float

@strawberry.input
class RecipeIngredientsInput:
  nic_profile_identifier: NicProfileIdentifierInput
  batch_volume_ml: float
  
@strawberry.type
class RecipeIngredientGroup:
  ingredients: list[RecipeIngredientType]
  total_pg_ratio: float
  total_vg_ratio: float