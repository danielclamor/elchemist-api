from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
import strawberry

from api_graphql.resolvers.utils import convert_strawberry_input_to_dict

from api_graphql.types.recipe import (
  MixParametersType,
  MixParametersFlavoringType,
  MixParametersNicBaseType,
  RecipeIngredientsOverrideInput,
  RecipeType,
  RecipeIngredientType,
  RecipeIngredientGroup,
)

from typing import TYPE_CHECKING, Optional

from models import Formula

if TYPE_CHECKING:
  from api_graphql.types.recipe import RecipeInput, RecipeDiyInput
  from api_graphql.types.formula import FormulaIdentifierInput

VG_FLAVOR_DENSITY = 1.16065
PG_FLAVOR_DENSITY = 1.04865
VG_DENSITY = 1.26130
PG_DENSITY = 1.03730
NIC_DENSITY = 1.00925

def build_mix_parameters(formula: Formula, batch_volume_ml: float, overrides: Optional[RecipeIngredientsOverrideInput] = None) -> MixParametersType:
  mix_parameters = MixParametersType(
    batch_volume_ml=batch_volume_ml,
    target_nic_str=float(formula.target_nic_str),
    target_vg=float(formula.target_vg),
    target_pg=float(formula.target_pg),
    nic_base_nic_str=float(formula.nic_base_nic_str),
    flavorings=[
      MixParametersFlavoringType(
        id=f"flavoring-{i}",
        slug=f.flavoring_option.slug,
        name=f.flavoring_option.name,
        is_vg=f.flavoring_option.is_vg,
        ratio=float(f.ratio),
      ) for i, f in enumerate(formula.flavorings, start=1)
    ],
    nic_bases=[
      MixParametersNicBaseType(
        id=f"nicbase-{i}",
        code=b.nic_base_option.code,
        name=b.nic_base_option.name,
        is_vg=b.nic_base_option.is_vg,
        ratio=float(b.ratio),
      ) for i, b in enumerate(formula.nic_bases, start=1)
    ]
  )
  
  if overrides is None or overrides is strawberry.UNSET:
    return mix_parameters
  if not isinstance(overrides, dict):
    overrides = convert_strawberry_input_to_dict(overrides)   # input object -> dict

  OVERRIDE_TRANSFORMS = {
    "flavorings": lambda value: [
      MixParametersFlavoringType(
        id=f"flavoring-{i}",
        slug=v.get("slug") if v.get("slug") not in (None, strawberry.UNSET) else None,
        name=v["name"],
        is_vg=v["is_vg"],
        ratio=v["ratio"])
      for i, v in enumerate(value, start=1)
    ],
    "nic_bases": lambda value: [
      MixParametersNicBaseType(
        id=f"nicbase-{i}",
        code=v.get("code") if v.get("code") not in (None, strawberry.UNSET) else None,
        name=v["name"],
        is_vg=v["is_vg"],
        ratio=v["ratio"])
      for i, v in enumerate(value, start=1)
    ],
  }

  for attr, value in overrides.items():
    if value is None or value is strawberry.UNSET:
      continue
    setattr(mix_parameters, attr, OVERRIDE_TRANSFORMS.get(attr, lambda v: v)(value))

  return mix_parameters

def build_recipe(mix_parameters: MixParametersType) -> RecipeType:
  ingredients = get_recipe_ingredients(mix_parameters=mix_parameters)
  return RecipeType(
    mix_parameters=mix_parameters,
    ingredients=ingredients,
    total_ratio=_round_float(sum(i.ratio for i in ingredients)),
    total_volume_ml=_round_float(sum(i.volume_ml for i in ingredients)),
    total_weight_g=_round_float(sum(i.weight_g for i in ingredients)),
  )

def get_recipe(db: Session, formula_identifier: "FormulaIdentifierInput", input: "RecipeInput") -> RecipeType | None:
  formula = db.scalar(select(Formula).where(formula_identifier.query_condition))
    
  if formula is None:
    return None
  
  return build_recipe(
    build_mix_parameters(
      formula=formula,
      batch_volume_ml=input.batch_volume_ml,
      overrides=input.overrides,
    )
  )

def get_recipe_diy(input: RecipeDiyInput) -> RecipeType:
  mix_parameters = MixParametersType(
    batch_volume_ml=input.batch_volume_ml,
    target_nic_str=float(input.target_nic_str),
    target_vg=float(input.target_vg),
    target_pg=float(input.target_pg),
    nic_base_nic_str=float(input.nic_base_nic_str),
    flavorings=[
      MixParametersFlavoringType(
        id=f"flavoring-{i}",
        name=f.name,
        is_vg=f.is_vg,
        ratio=float(f.ratio),
      ) for i, f in enumerate(input.flavorings, start=1)
    ],
    nic_bases=[
      MixParametersNicBaseType(
        id=f"nicbase-1",
        code="PG",
        name="PG",
        is_vg=False,
        ratio=float(input.nic_base_pg),
      ),
      MixParametersNicBaseType(
        id=f"nicbase-2",
        code="VG",
        name="VG",
        is_vg=True,
        ratio=float(input.nic_base_vg),
      ),
    ],
  )
    
  return build_recipe(mix_parameters=mix_parameters)

def get_recipe_ingredients(mix_parameters: MixParametersType) -> list[RecipeIngredientType]:  
  nic_base_ingredients = get_nic_base_ingredients(
    nic_bases=mix_parameters.nic_bases,
    batch_volume_ml=mix_parameters.batch_volume_ml, 
    target_nic_str=mix_parameters.target_nic_str, 
    nic_base_nic_str=mix_parameters.nic_base_nic_str
  )
  
  flavoring_ingredients = get_flavoring_ingredients(
    flavorings=mix_parameters.flavorings,
    batch_volume_ml=mix_parameters.batch_volume_ml
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

def _round_float(value: float, ndigits: Optional[int] = 2) -> float:
  return round(value, ndigits)

def get_nic_base_ingredients(nic_bases: list[MixParametersNicBaseType], batch_volume_ml: float, target_nic_str: float, nic_base_nic_str: float) -> RecipeIngredientGroup:
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
    
    if nic_base_ratio <= 0:
      continue
    
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
        ratio=_round_float(nic_base_batch_ratio),
        volume_ml=_round_float(nic_base_batch_volume_ml),
        weight_g=_round_float(nic_base_batch_weight_g)
      )
    )
  
  return RecipeIngredientGroup(
    ingredients=ingredients,
    total_pg_ratio=total_pg_ratio,
    total_vg_ratio=total_vg_ratio
  )
  
def get_flavoring_ingredients(flavorings: list[MixParametersFlavoringType], batch_volume_ml: float) -> RecipeIngredientGroup:
  ingredients = []
  total_pg_ratio = 0.0
  total_vg_ratio = 0.0
  
  for flavoring in flavorings:
    flavoring_ratio = flavoring.ratio
    
    if flavoring_ratio <= 0:
      continue
    
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
        ratio=_round_float(flavoring_ratio),
        volume_ml=_round_float(volume_ml),
        weight_g=_round_float(weight_g)
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
    ratio=_round_float(pg_ratio),
    volume_ml=_round_float(volume_ml),
    weight_g=_round_float(weight_g)
  )

def get_vg_ingredient(
  total_vg_flavoring_batch_ratio: float, total_vg_nic_base_batch_ratio: float, target_nic_str: float, target_vg: float, nic_base_nic_str: float, batch_volume_ml: float
) -> RecipeIngredientType:
  vg_ratio = target_vg - total_vg_flavoring_batch_ratio + (target_nic_str * (total_vg_nic_base_batch_ratio - target_vg - (total_vg_nic_base_batch_ratio / nic_base_nic_str)))
  volume_ml = vg_ratio * batch_volume_ml
  weight_g = volume_ml * VG_DENSITY
  
  return RecipeIngredientType(
    name="VG",
    ratio=_round_float(vg_ratio),
    volume_ml=_round_float(volume_ml),
    weight_g=_round_float(weight_g)
  )