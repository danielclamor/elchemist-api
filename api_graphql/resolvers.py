from sqlalchemy.orm import Session, joinedload
import models
from api_graphql.graphql_types import FormulaType, NicProfileType, NicBaseType, NicBaseOptionType, FlavoringType, ChillType, NicType

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
        flavorings=[FlavoringType(name=fl.name, ratio=fl.ratio, is_vg=fl.is_vg) for fl in p.flavorings],
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