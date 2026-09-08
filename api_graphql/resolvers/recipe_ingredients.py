from __future__ import annotations

from graphql import GraphQLError
from sqlalchemy.orm import Session

from models import (
  NicBase,
  Flavoring,
)

from api_graphql.types.recipe_ingredients import RecipeIngredientType, RecipeIngredientGroup

from api_graphql.resolvers.nic_profile import get_nic_profile

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from api_graphql.types.nic_profile import NicProfileIdentifierInput

VG_FLAVOR_DENSITY = 1.16065
PG_FLAVOR_DENSITY = 1.04865
VG_DENSITY = 1.26130
PG_DENSITY = 1.03730
NIC_DENSITY = 1.00925

def get_recipe_ingredients(db: Session, nic_profile_identifier: "NicProfileIdentifierInput", batch_volume_ml: float) -> list[RecipeIngredientType]:
  nic_profile = get_nic_profile(db=db, identifier=nic_profile_identifier)
  
  if nic_profile is None:
    raise GraphQLError(f"NicProfile not found for identifier: {nic_profile_identifier}")
  
  target_nic_str = float(nic_profile.target_nic_str)
  target_vg = float(nic_profile.target_vg)
  target_pg = float(nic_profile.target_pg)
  nic_base_nic_str = float(nic_profile.nic_base_nic_str)
  
  flavoring_ingredients = get_flavoring_ingredients(
    flavorings=nic_profile.flavorings, 
    batch_volume_ml=batch_volume_ml
  )
  
  nic_base_ingredients = get_nic_base_ingredients(
    nic_bases=nic_profile.nic_bases, 
    batch_volume_ml=batch_volume_ml, 
    target_nic_str=target_nic_str, 
    nic_base_nic_str=nic_base_nic_str
  )
  
  pg_ingredient = get_pg_ingredient(
    total_pg_flavoring_batch_ratio=flavoring_ingredients.total_pg_ratio,
    total_pg_nic_base_batch_ratio=nic_base_ingredients.total_pg_ratio,
    target_nic_str=target_nic_str,
    target_pg=target_pg,
    nic_base_nic_str=nic_base_nic_str,
    batch_volume_ml=batch_volume_ml
  )
  
  vg_ingredient = get_vg_ingredient(
    total_vg_flavoring_batch_ratio=flavoring_ingredients.total_vg_ratio,
    total_vg_nic_base_batch_ratio=nic_base_ingredients.total_vg_ratio,
    target_nic_str=target_nic_str,
    target_vg=target_vg,
    nic_base_nic_str=nic_base_nic_str,
    batch_volume_ml=batch_volume_ml
  )
  
  return nic_base_ingredients.ingredients + flavoring_ingredients.ingredients + [pg_ingredient, vg_ingredient]

def get_flavoring_ingredients(flavorings: list[Flavoring], batch_volume_ml: float) -> RecipeIngredientGroup:
  ingredients = []
  total_pg_ratio = 0.0
  total_vg_ratio = 0.0
  
  for flavoring in flavorings:
    flavoring_ratio = float(flavoring.ratio)
    volume_ml = flavoring_ratio * batch_volume_ml
    
    flavoring_option = flavoring.flavoring_option
    
    if flavoring_option.is_vg is True:
      total_vg_ratio += flavoring_ratio
      weight_g = volume_ml * VG_FLAVOR_DENSITY # vg flavor density
    else:
      total_pg_ratio += flavoring_ratio
      weight_g = volume_ml * PG_FLAVOR_DENSITY # pg flavor density
    
    ingredients.append(
      RecipeIngredientType(
        name=flavoring_option.name,
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

def get_nic_base_ingredients(nic_bases: list[NicBase], batch_volume_ml: float, target_nic_str: float, nic_base_nic_str: float) -> RecipeIngredientGroup:
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
    nic_base_option = nic_base.nic_base_option
    nic_base_ratio = float(nic_base.ratio)
    
    nic_base_batch_ratio = (target_nic_str / nic_base_nic_str) * nic_base_ratio
    nic_base_nic_batch_ratio = target_nic_str * nic_base_ratio
    
    nic_base_part_volume_ml = batch_volume_ml * (nic_base_batch_ratio - nic_base_nic_batch_ratio)
    nic_base_nic_volume_ml = batch_volume_ml * nic_base_nic_batch_ratio
    nic_base_batch_volume_ml = nic_base_part_volume_ml + nic_base_nic_volume_ml
    
    nic_base_nic_weight_g = nic_base_nic_volume_ml * NIC_DENSITY
    
    if nic_base_option.is_vg is True:
      total_vg_ratio += nic_base_ratio
      nic_base_vg_part_weight_g = nic_base_part_volume_ml * VG_DENSITY
      nic_base_batch_weight_g = nic_base_nic_weight_g + nic_base_vg_part_weight_g
    else:
      total_pg_ratio += nic_base_ratio
      nic_base_pg_part_weight_g = nic_base_part_volume_ml * PG_DENSITY
      nic_base_batch_weight_g = nic_base_nic_weight_g + nic_base_pg_part_weight_g
    
    ingredients.append(
      RecipeIngredientType(
        name=f"Nic Base ({nic_base_option.code})",
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
  weight_g = volume_ml * PG_DENSITY # pg density
  
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
  weight_g = volume_ml * VG_DENSITY # vg density
  
  return RecipeIngredientType(
    name="VG",
    ratio=vg_ratio,
    volume_ml=volume_ml,
    weight_g=weight_g
  )