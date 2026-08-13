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

def get_flavoring_option(db: Session, flavoring_option_slug: str) -> models.FlavoringOption:
  return (
    db.scalar(select(models.FlavoringOption).where(models.FlavoringOption.slug == flavoring_option_slug))
  )

def get_all_flavoring_options(db: Session) -> list[models.FlavoringOption]:
  return (
    db.query(models.FlavoringOption).all()
  )


# Mutation resolvers
def create_flavoring_option(db: Session, flavoring_option_slug: str, flavoring_option_name: str, is_vg: bool | None = None) -> models.FlavoringOption | Feedback:
  if is_vg is None:
    return Feedback(
      status=FeedbackStatus.CANCELLED,
      message=f"Can't create flavoring option {flavoring_option_slug} without isVg"
    )
    
  flavoring_option = models.FlavoringOption(
    slug=flavoring_option_slug,
    name=flavoring_option_name,
    is_vg=is_vg,
  )
  
  db.add(flavoring_option)
  db.commit()
  db.refresh(flavoring_option)
  return flavoring_option

def add_nic_profile_flavoring(db: Session, nic_profile_slug: str, flavoring_option_name: str, ratio: float, is_vg: bool | None = None) -> NicProfileAddFlavoringPayload:
  nic_profile = db.scalar(select(models.NicProfile).where(models.NicProfile.slug == nic_profile_slug))
  if not nic_profile:
    return NicProfileAddFlavoringPayload(
      nic_profile=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Nic Profile {nic_profile_slug} not found",
      )
    )
  
  flavoring_option_slug = make_slug(flavoring_option_name)
  existing_flavoring_option = get_flavoring_option(db=db, flavoring_option_slug=flavoring_option_slug)
  if not existing_flavoring_option:
    existing_flavoring_option = create_flavoring_option(
      db=db,
      flavoring_option_slug=flavoring_option_slug,
      flavoring_option_name=flavoring_option_name,
      is_vg=is_vg
    )
    
    if isinstance(existing_flavoring_option, Feedback):
      return NicProfileAddFlavoringPayload(
        nic_profile=nic_profile_to_type(nic_profile),
        feedback=existing_flavoring_option,
      )
    
  existing_flavoring = db.scalar(select(models.Flavoring).where(models.Flavoring.flavoring_option_id == existing_flavoring_option.id, models.Flavoring.nic_profile_id == nic_profile.id))
  if existing_flavoring:
    return NicProfileAddFlavoringPayload(
      nic_profile=nic_profile_to_type(nic_profile),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Flavoring {existing_flavoring_option.name} is already connected"
      )
    )
  
  flavoring = models.Flavoring(
    nic_profile_id=nic_profile.id,
    flavoring_option_id=existing_flavoring_option.id,
    ratio=ratio
  )
  
  db.add(flavoring)
  db.commit()
  db.refresh(flavoring)
  return NicProfileAddFlavoringPayload(
    nic_profile=nic_profile_to_type(nic_profile),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=f"Flavoring {existing_flavoring_option.name} added to {nic_profile.full_name}"
    )
  ) 

def create_nic_profile(db: Session, formula_slug: str, name: str, nic_base_str: float, is_old_mix: bool, target_nic_str: float, target_vg: float, target_pg: float) -> NicProfileCreatePayload:
  formula = db.scalar(select(models.Formula).where(models.Formula.slug == formula_slug))
  if not formula:
    return NicProfileCreatePayload(
      nic_profile=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Formula {formula_slug} not found",
      )
    )
    
  suffix = " - Old Mix" if is_old_mix else ""
  full_name = f"{formula.name} - {name}{suffix}"
  slug = make_slug(full_name)
  
  existing = db.scalar(select(models.NicProfile).where(models.NicProfile.slug == slug, 
                                                       models.NicProfile.formula_id == formula.id))
  if existing:
    return NicProfileCreatePayload(
      nic_profile=nic_profile_to_type(existing),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Nic Profile {slug} already exists",
      )
    )
  
  nic_profile = models.NicProfile(
    formula_id=formula.id,
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
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )
  
def create_formula(db: Session, name: str, brand: str, chill_type: ChillType, nic_type: NicType) -> FormulaCreatePayload:
  slug = make_slug(string=name)
  
  existing = db.scalar(select(models.Formula).where(models.Formula.slug == slug))
  if existing:
    print(f"Canceling — formula {slug!r} already exists")
    return FormulaCreatePayload(
      formula=formula_to_type(existing),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Formula {slug} already existss",
      )
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
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )