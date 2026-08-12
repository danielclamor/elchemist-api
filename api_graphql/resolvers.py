from sqlalchemy.orm import Session, joinedload
import models
from api_graphql.graphql_types import FlavoringOptionType, FormulaType, NicProfileType, NicBaseType, NicBaseOptionType, FlavoringType, ChillType, NicType

def formula_to_type(f: models.Formula) -> FormulaType:
    return FormulaType(
        slug=f.slug,
        name=f.name,
        brand=f.brand,
        
        chill_type=ChillType[f.chill_type.name],
        nic_type=NicType[f.nic_type.name],
        
        nic_profiles=[nic_profile_to_type(p) for p in f.nic_profiles],
    )

def nic_profile_to_type(p: models.NicProfile) -> NicProfileType:
    return NicProfileType(
        slug=p.slug,
        name=p.name,
        full_name=p.full_name,
        is_new_mix=p.is_new_mix,
        target_nic_str=p.target_nic_str,
        target_vg=p.target_vg,
        target_pg=p.target_pg,
        nic_base_nic_str=p.nic_base_nic_str,
        nic_bases=[
            NicBaseType(
                ratio=nb.ratio,
                nic_base_option=NicBaseOptionType(code=nb.nic_base_option.code, name=nb.nic_base_option.name, is_vg=nb.nic_base_option.is_vg),
            )
            for nb in p.nic_bases
        ],
        flavorings=[FlavoringType(flavoring_option=FlavoringOptionType(slug=fl.flavoring_option.slug, name=fl.flavoring_option.name, is_vg=fl.flavoring_option.is_vg), ratio=fl.ratio) for fl in p.flavorings],
    )
    
def get_all_formulas(db: Session) -> list[models.Formula]:
    return (
        db.query(models.Formula)
        .options(
            joinedload(models.Formula.nic_profiles)
            .joinedload(models.NicProfile.nic_bases)
            .joinedload(models.NicBase.nic_base_option),
            joinedload(models.Formula.nic_profiles)
            .joinedload(models.NicProfile.flavorings),
        )
        .all()
    )
    
def nic_base_option_to_type(o: models.NicBaseOption) -> NicBaseOptionType:
  return NicBaseOptionType(
    code=o.code,
    name=o.name,
    is_vg=o.is_vg,
  )

def get_all_nic_base_options(db: Session) -> list[models.NicBaseOption]:
  return (
    db.query(models.NicBaseOption).all()
  )
  
def flavoring_option_to_type(o: models.FlavoringOption) -> FlavoringOptionType:
  return FlavoringOptionType(
    slug=o.slug,
    name=o.name,
    is_vg=o.is_vg,
  )

def get_all_flavoring_options(db: Session) -> list[models.FlavoringOption]:
  return (
    db.query(models.FlavoringOption).all()
  )