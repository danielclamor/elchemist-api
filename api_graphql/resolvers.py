from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
import models
from api_graphql.graphql_types import *
  
  
# Auxiliary functions  
def make_slug(string: str) -> str:
  import re
  tokens = re.sub(r'[^a-zA-Z0-9]', ' ', string).strip().split(' ')
  tokens = [token for token in tokens if token != ""]
  return '-'.join(tokens).lower()


# SQLAlchemy model -> GraphQL model resolvers
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
        is_old_mix=p.is_old_mix,
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
    
def nic_base_option_to_type(o: models.NicBaseOption) -> NicBaseOptionType:
  return NicBaseOptionType(
    code=o.code,
    name=o.name,
    is_vg=o.is_vg,
  )
  
def flavoring_option_to_type(o: models.FlavoringOption) -> FlavoringOptionType:
  return FlavoringOptionType(
    slug=o.slug,
    name=o.name,
    is_vg=o.is_vg,
  )
  

# Query resolvers
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

def get_all_nic_base_options(db: Session) -> list[models.NicBaseOption]:
  return (
    db.query(models.NicBaseOption).all()
  )

def get_all_flavoring_options(db: Session) -> list[models.FlavoringOption]:
  return (
    db.query(models.FlavoringOption).all()
  )


# Mutation resolvers
def create_nic_profile(db: Session, formula_slug: str, name: str, nic_base_str: float, is_old_mix: bool, target_nic_str: float, target_vg: float, target_pg: float) -> NicProfileCreatePayload:
  formula = db.scalar(select(models.Formula).where(models.Formula.slug == formula_slug))
  if not formula:
    return NicProfileCreatePayload(
      nic_profile=None,
      created=False,
      message=f"Formula {formula_slug} not found",
    )
    
  suffix = " - Old Mix" if is_old_mix else ""
  full_name = f"{formula.name} - {name}{suffix}"
  slug = make_slug(full_name)
  
  existing = db.scalar(select(models.NicProfile).where(models.NicProfile.slug == slug, 
                                                       models.NicProfile.formula_id == formula.id))
  if existing:
    return NicProfileCreatePayload(
      nic_profile=nic_profile_to_type(existing),
      created=False,
      message=f"Nic Profile {slug} already exists",
    )
  
  nic_profile = models.NicProfile(
    formula_id = formula.id,
    slug=slug,
    full_name=full_name,
    name=name,
    is_old_mix=is_old_mix,
    nic_base_nic_str=nic_base_str,
    target_nic_str=target_nic_str,
    target_vg=target_vg,
    target_pg=target_pg,
  )
  
  db.add(nic_profile)
  db.commit()
  db.refresh(nic_profile)
  return NicProfileCreatePayload(
    nic_profile=nic_profile_to_type(nic_profile),
    created=True,
    message=None,
  )
  
  
def create_formula(db: Session, name: str, brand: str, chill_type: ChillType, nic_type: NicType) -> FormulaCreatePayload:
  slug = make_slug(string=name)
  
  existing = db.scalar(select(models.Formula).where(models.Formula.slug == slug))
  if existing:
    print(f"Canceling — formula {slug!r} already exists")
    return FormulaCreatePayload(
      formula=formula_to_type(existing),
      created=False, 
      message=f"Formula {slug} already exists",
    )
    
  formula = models.Formula(
    slug=slug,
    name=name,
    brand=brand,
    chill_type=models.ChillType[chill_type.name],
    nic_type=models.NicType[nic_type.name],
  )
  
  db.add(formula)
  db.commit()
  db.refresh(formula)
  return FormulaCreatePayload(
      formula=formula_to_type(formula),
      created=True, 
      message=None,
  )