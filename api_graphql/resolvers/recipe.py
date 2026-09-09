from __future__ import annotations

from graphql import GraphQLError
from sqlalchemy.orm import Session
import strawberry

from api_graphql.types.recipe import (
  MixParametersType,
  MixParametersFlavorings,
  MixParametersNicBases,
  RecipeType,
  RecipeDiyType,
  RecipeIngredientType,
  RecipeIngredientGroup,
)

from api_graphql.types.nic_profile import NicProfileType

from api_graphql.resolvers.nic_profile import get_nic_profile

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from api_graphql.types.recipe import RecipeInput, RecipeDiyInput
  from api_graphql.types.nic_profile import NicProfileIdentifierInput

VG_FLAVOR_DENSITY = 1.16065
PG_FLAVOR_DENSITY = 1.04865
VG_DENSITY = 1.26130
PG_DENSITY = 1.03730
NIC_DENSITY = 1.00925  

def get_recipe(db: Session, nic_profile_identifier: "NicProfileIdentifierInput", input: "RecipeInput") -> RecipeType:
  nic_profile = get_nic_profile(db=db, identifier=nic_profile_identifier)
    
  if nic_profile is None:
    raise GraphQLError(f"NicProfile not found for identifier: {nic_profile_identifier}")
  
  mix_parameters = MixParametersType(
    batch_volume_ml=input.batch_volume_ml,
    target_nic_str=float(nic_profile.target_nic_str),
    target_vg=float(nic_profile.target_vg),
    target_pg=float(nic_profile.target_pg),
    nic_base_nic_str=float(nic_profile.nic_base_nic_str),
    flavorings=[
      MixParametersFlavorings(
        name=f.flavoring_option.name,
        is_vg=f.flavoring_option.is_vg,
        ratio=float(f.ratio),
      ) for f in nic_profile.flavorings
    ],
    nic_bases=[
      MixParametersNicBases(
        code=b.nic_base_option.code,
        name=b.nic_base_option.name,
        is_vg=b.nic_base_option.is_vg,
        ratio=float(b.ratio),
      ) for b in nic_profile.nic_bases
    ]
  )
  
  if input.overrides is not strawberry.UNSET:
    OVERRIDE_TRANSFORMS = {
      "flavorings": lambda value: [
        MixParametersFlavorings(
          name=v.name,
          is_vg=v.is_vg,
          ratio=v.ratio
        ) for v in value
      ],
      "nic_bases": lambda value: [
        MixParametersNicBases(
          code=v.code,
          name=v.name,
          is_vg=v.is_vg,
          ratio=v.ratio
        ) for v in value
      ],
    }
    
    for attr, value in vars(input.overrides).items():
      if value is strawberry.UNSET:
        continue
      
      transform = OVERRIDE_TRANSFORMS.get(attr)
      if transform:
        value = transform(value)
      
      setattr(mix_parameters, attr, value)
  
  ingredients = get_recipe_ingredients(mix_parameters=mix_parameters)
  
  return RecipeType(
    mix_parameters=mix_parameters,
    ingredients=ingredients,
    total_ratio=sum(i.ratio for i in ingredients),
    total_volume_ml=sum(i.volume_ml for i in ingredients),
    total_weight_g=sum(i.weight_g for i in ingredients),
    nic_profile=NicProfileType.from_model(nic_profile)
  )

def get_recipe_diy(input: RecipeDiyInput) -> RecipeDiyType:
  mix_parameters = MixParametersType(
    batch_volume_ml=input.batch_volume_ml,
    target_nic_str=float(input.target_nic_str),
    target_vg=float(input.target_vg),
    target_pg=float(input.target_pg),
    nic_base_nic_str=float(input.nic_base_nic_str),
    flavorings=[
      MixParametersFlavorings(
        name=f.name,
        is_vg=f.is_vg,
        ratio=float(f.ratio),
      ) for f in input.flavorings
    ],
    nic_bases=[
      MixParametersNicBases(
        code="PG",
        name="PG",
        is_vg=False,
        ratio=float(input.nic_base_pg),
      ),
      MixParametersNicBases(
        code="VG",
        name="VG",
        is_vg=True,
        ratio=float(input.nic_base_vg),
      ),
    ],
  )
  
  ingredients = get_recipe_ingredients(mix_parameters=mix_parameters)
    
  return RecipeDiyType(
    mix_parameters=mix_parameters,
    ingredients=ingredients,
    total_ratio=sum(i.ratio for i in ingredients),
    total_volume_ml=sum(i.volume_ml for i in ingredients),
    total_weight_g=sum(i.weight_g for i in ingredients),
  )

def get_recipe_ingredients(mix_parameters: MixParametersType) -> list[RecipeIngredientType]:  
  flavoring_ingredients = get_flavoring_ingredients(
    flavorings=mix_parameters.flavorings,
    batch_volume_ml=mix_parameters.batch_volume_ml
  )
  
  nic_base_ingredients = get_nic_base_ingredients(
    nic_bases=mix_parameters.nic_bases,
    batch_volume_ml=mix_parameters.batch_volume_ml, 
    target_nic_str=mix_parameters.target_nic_str, 
    nic_base_nic_str=mix_parameters.nic_base_nic_str
  )
  
  pg_ingredient = get_pg_ingredient(
    total_pg_flavoring_batch_ratio=flavoring_ingredients.total_pg_ratio,
    total_pg_nic_base_batch_ratio=nic_base_ingredients.total_pg_ratio,
    target_nic_str=mix_parameters.target_nic_str,
    target_pg=mix_parameters.target_pg,
    nic_base_nic_str=mix_parameters.nic_base_nic_str,
    batch_volume_ml=mix_parameters.batch_volume_ml
  )
  
  vg_ingredient = get_vg_ingredient(
    total_vg_flavoring_batch_ratio=flavoring_ingredients.total_vg_ratio,
    total_vg_nic_base_batch_ratio=nic_base_ingredients.total_vg_ratio,
    target_nic_str=mix_parameters.target_nic_str,
    target_vg=mix_parameters.target_vg,
    nic_base_nic_str=mix_parameters.nic_base_nic_str,
    batch_volume_ml=mix_parameters.batch_volume_ml
  )
  
  return nic_base_ingredients.ingredients + flavoring_ingredients.ingredients + [vg_ingredient, pg_ingredient]

def get_flavoring_ingredients(flavorings: list[MixParametersFlavorings], batch_volume_ml: float) -> RecipeIngredientGroup:
  ingredients = []
  total_pg_ratio = 0.0
  total_vg_ratio = 0.0
  
  for flavoring in flavorings:
    flavoring_ratio = flavoring.ratio
    volume_ml = flavoring_ratio * batch_volume_ml
    
    if flavoring.is_vg is True:
      total_vg_ratio += flavoring_ratio
      weight_g = volume_ml * VG_FLAVOR_DENSITY
    else:
      total_pg_ratio += flavoring_ratio
      weight_g = volume_ml * PG_FLAVOR_DENSITY
    
    ingredients.append(
      RecipeIngredientType(
        name=flavoring.name,
        ratio=flavoring_ratio,
        volume_ml=volume_ml,
        weight_g=weight_g
      )
    )
  
  return RecipeIngredientGroup(
    ingredients=ingredients,
    total_pg_ratio=total_pg_ratio,
    total_vg_ratio=total_vg_ratio
  )

def get_nic_base_ingredients(nic_bases: list[MixParametersNicBases], batch_volume_ml: float, target_nic_str: float, nic_base_nic_str: float) -> RecipeIngredientGroup:
  ingredients = []
  total_pg_ratio = 0.0
  total_vg_ratio = 0.0
  
  if nic_base_nic_str == 0:
    return RecipeIngredientGroup(
    ingredients=ingredients,
    total_pg_ratio=total_pg_ratio,
    total_vg_ratio=total_vg_ratio
  )
  
  for nic_base in nic_bases:
    nic_base_ratio = nic_base.ratio
    
    nic_base_batch_ratio = (target_nic_str / nic_base_nic_str) * nic_base_ratio
    nic_base_nic_batch_ratio = target_nic_str * nic_base_ratio
    
    nic_base_part_volume_ml = batch_volume_ml * (nic_base_batch_ratio - nic_base_nic_batch_ratio)
    nic_base_nic_volume_ml = batch_volume_ml * nic_base_nic_batch_ratio
    nic_base_batch_volume_ml = nic_base_part_volume_ml + nic_base_nic_volume_ml
    
    nic_base_nic_weight_g = nic_base_nic_volume_ml * NIC_DENSITY
    
    if nic_base.is_vg is True:
      total_vg_ratio += nic_base_ratio
      nic_base_vg_part_weight_g = nic_base_part_volume_ml * VG_DENSITY
      nic_base_batch_weight_g = nic_base_nic_weight_g + nic_base_vg_part_weight_g
    else:
      total_pg_ratio += nic_base_ratio
      nic_base_pg_part_weight_g = nic_base_part_volume_ml * PG_DENSITY
      nic_base_batch_weight_g = nic_base_nic_weight_g + nic_base_pg_part_weight_g
    
    ingredients.append(
      RecipeIngredientType(
        name=f"Nic Base ({nic_base.code})",
        ratio=nic_base_batch_ratio,
        volume_ml=nic_base_batch_volume_ml,
        weight_g=nic_base_batch_weight_g
      )
    )
  
  return RecipeIngredientGroup(
    ingredients=ingredients,
    total_pg_ratio=total_pg_ratio,
    total_vg_ratio=total_vg_ratio
  )
  
def get_pg_ingredient(
  total_pg_flavoring_batch_ratio: float, total_pg_nic_base_batch_ratio: float, target_nic_str: float, target_pg: float, nic_base_nic_str: float, batch_volume_ml: float
) -> RecipeIngredientType:
  pg_ratio = target_pg - total_pg_flavoring_batch_ratio + (target_nic_str * (total_pg_nic_base_batch_ratio - target_pg - (total_pg_nic_base_batch_ratio / nic_base_nic_str)))
  volume_ml = pg_ratio * batch_volume_ml
  weight_g = volume_ml * PG_DENSITY
  
  return RecipeIngredientType(
    name="PG",
    ratio=pg_ratio,
    volume_ml=volume_ml,
    weight_g=weight_g
  )

def get_vg_ingredient(
  total_vg_flavoring_batch_ratio: float, total_vg_nic_base_batch_ratio: float, target_nic_str: float, target_vg: float, nic_base_nic_str: float, batch_volume_ml: float
) -> RecipeIngredientType:
  vg_ratio = target_vg - total_vg_flavoring_batch_ratio + (target_nic_str * (total_vg_nic_base_batch_ratio - target_vg - (total_vg_nic_base_batch_ratio / nic_base_nic_str)))
  volume_ml = vg_ratio * batch_volume_ml
  weight_g = volume_ml * VG_DENSITY
  
  return RecipeIngredientType(
    name="VG",
    ratio=vg_ratio,
    volume_ml=volume_ml,
    weight_g=weight_g
  )