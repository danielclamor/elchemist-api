from __future__ import annotations
from enum import Enum
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, select
import strawberry

from .utils import generate_slug

from models import (
  Formula,
  NicProfile,
  Flavoring,
  NicBase,
)

from api_graphql.resolvers.flavoring_option import (
  get_flavoring_option,
)

from api_graphql.resolvers.nic_base_option import (
  get_nic_base_option,
)

from api_graphql.types.feedback import Feedback, FeedbackStatus

from api_graphql.types.nic_profile import (
  NicProfileType,
  NicProfileCreatePayload,
  NicProfileDeletePayload,
  NicProfileUpdatePayload,
  NicProfileFlavoringType,
  NicProfileFlavoringAddPayload,
  NicProfileFlavoringsBulkAddPayload,
  NicProfileFlavoringsBulkRemovePayload,
  NicProfileFlavoringRemovePayload,
  NicProfileNicBaseType,
  NicProfileNicBaseAddPayload,
  NicProfileNicBasesBulkAddPayload,
  NicProfileNicBasesBulkRemovePayload,
  NicProfileNicBaseRemovePayload,
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from api_graphql.types.formula import FormulaIdentifierInput
  
  from api_graphql.types.nic_profile import (
    NicProfileIdentifierInput,
    NicProfileCreateInput,
    NicProfileUpdateInput,
    NicProfileFlavoringIdentifierInput,
    NicProfileFlavoringInput,
    NicProfileNicBaseIdentifierInput,
    NicProfileNicBaseInput,
  )
  
  
# Queries
def get_all_nic_profiles(db: Session) -> list[NicProfile]:
  return (
    db.scalars(select(NicProfile))
    .unique()
    .all()
  )

def get_nic_profile(db: Session, identifier: "NicProfileIdentifierInput") -> NicProfile:
  return (
    db.scalar(select(NicProfile).where(identifier.query_condition))
  )
  
  
# Mutations
def add_nic_profile_flavoring(db: Session, id: uuid.UUID, input: "NicProfileFlavoringInput") -> NicProfileFlavoringAddPayload:
  flavoring_option = get_flavoring_option(db=db, identifier=input.flavoring_option_identifier)
  
  if not flavoring_option:
    return NicProfileFlavoringAddPayload(
      nic_profile_flavoring=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"FlavoringOption {input.flavoring_option_identifier.provided[1]} not found."
      )
    )
    
  existing = db.scalar(
    select(Flavoring).where(
      and_(
        Flavoring.flavoring_option_id == flavoring_option.id,
        Flavoring.nic_profile_id == id,
      )
    )
  )
  
  if existing:
    return NicProfileFlavoringAddPayload(
      nic_profile_flavoring=NicProfileFlavoringType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Flavoring {existing.name} is already connected with ratio {existing.ratio}"
      )
    )

  flavoring = Flavoring(
    nic_profile_id=id,
    flavoring_option_id=flavoring_option.id,
    ratio=input.ratio,
  )

  db.add(flavoring)
  db.commit()
  db.refresh(flavoring)
  
  return NicProfileFlavoringAddPayload(
    nic_profile_flavoring=NicProfileFlavoringType.from_model(flavoring),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def add_nic_profile_nic_base(db: Session, id: uuid.UUID, input: "NicProfileNicBaseInput") -> NicProfileNicBaseAddPayload:
  nic_base_option = get_nic_base_option(db=db, identifier=input.nic_base_option_identifier)
  
  if not nic_base_option:
    return NicProfileNicBaseAddPayload(
      nic_profile_nic_base=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"NicBaseOption {input.nic_base_option_identifier.provided[1]} not found."
      )
    )
  
  existing = db.scalar(
    select(NicBase).where(
      and_(
        NicBase.nic_base_option_id == nic_base_option.id,
        NicBase.nic_profile_id == id,
      )
    )
  )
  
  if existing:
    return NicProfileNicBaseAddPayload(
      nic_profile_nic_base=NicProfileNicBaseType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"NicBase {existing.name} is already connected with ratio {existing.ratio}"
      )
    )
  
  nic_base = NicBase(
    nic_profile_id=id,
    nic_base_option_id=nic_base_option.id,
    ratio=input.ratio,
  )
  
  db.add(nic_base)
  db.commit()
  db.refresh(nic_base)
  
  return NicProfileNicBaseAddPayload(
    nic_profile_nic_base=NicProfileNicBaseType.from_model(nic_base),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def bulk_add_nic_profile_flavorings(db: Session, identifier: "NicProfileIdentifierInput", inputs: list["NicProfileFlavoringInput"]) -> NicProfileFlavoringsBulkAddPayload:
  nic_profile = get_nic_profile(db=db, identifier=identifier)
  
  if not nic_profile:
    return NicProfileFlavoringsBulkAddPayload(
      nic_profile_flavorings=[],
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"NicProfile {identifier.provided[1]} not found."
      )
    )
  
  if len(inputs) == 0:
    return NicProfileFlavoringsBulkAddPayload(
      nic_profile_flavorings=[],
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message="Nothing to add"
      )
    )
  
  flavorings = []
  
  for input in inputs:
    flavorings.append(add_nic_profile_flavoring(db=db, id=nic_profile.id, input=input))
    
  return NicProfileFlavoringsBulkAddPayload(
    nic_profile_flavorings=flavorings,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def bulk_add_nic_profile_nic_bases(db: Session, identifier: "NicProfileIdentifierInput", inputs: list["NicProfileNicBaseInput"]) -> NicProfileNicBasesBulkAddPayload:
  nic_profile = get_nic_profile(db=db, identifier=identifier)
  
  if not nic_profile:
    return NicProfileNicBasesBulkAddPayload(
      nic_profile_nic_bases=[],
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"NicProfile {identifier.provided[1]} not found."
      )
    )
    
  if len(inputs) == 0:
    return NicProfileNicBasesBulkAddPayload(
      nic_profile_nic_bases=[],
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message="Nothing to add"
      )
    )
  
  nic_bases = []
  
  for input in inputs:
    nic_bases.append(add_nic_profile_nic_base(db=db, id=nic_profile.id, input=input))
    
  return NicProfileNicBasesBulkAddPayload(
    nic_profile_nic_bases=nic_bases,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def bulk_remove_nic_profile_flavorings(db: Session, identifiers: list[NicProfileFlavoringIdentifierInput]) -> NicProfileFlavoringsBulkRemovePayload:
  removed = []
  
  if len(identifiers) == 0:
    return NicProfileFlavoringsBulkRemovePayload(
      nic_profile_flavorings=[],
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message="Nothing to remove.",
      )
    )
  
  for identifier in identifiers:
    removed.append(remove_nic_profile_flavoring(db=db, identifier=identifier))
    
  return NicProfileFlavoringsBulkRemovePayload(
    nic_profile_flavorings=removed,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def bulk_remove_nic_profile_nic_bases(db: Session, identifiers: list[NicProfileNicBaseIdentifierInput]) -> NicProfileNicBasesBulkRemovePayload:
  removed = []
  
  if len(identifiers) == 0:
    return NicProfileNicBasesBulkRemovePayload(
      nic_profile_nic_bases=[],
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message="Nothing to remove.",
      )
    )
  
  for identifier in identifiers:
    removed.append(remove_nic_profile_nic_base(db=db, identifier=identifier))
    
  return NicProfileNicBasesBulkRemovePayload(
    nic_profile_nic_bases=removed,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )
  
def create_nic_profile(db: Session, formula_identifier: "FormulaIdentifierInput", nic_profile: "NicProfileCreateInput") -> NicProfileCreatePayload:
  formula = db.scalar(select(Formula).where(formula_identifier.query_condition))
  
  if not formula:
    return NicProfileCreatePayload(
      nic_profile=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Formula {formula_identifier.provided[1]} not found.",
      )
    )

  suffix = " - Old Mix" if nic_profile.is_old_mix else ""
  full_name = f"{formula.name} - {nic_profile.name}{suffix}"
  slug = generate_slug(full_name)

  existing = db.scalar(
    select(NicProfile).where(
      and_(
        NicProfile.slug == slug,
        NicProfile.formula_id == formula.id
      )
    )
  )
  
  if existing:
    return NicProfileCreatePayload(
      nic_profile=NicProfileType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Nic Profile {slug} already exists",
      )
    )

  nic_profile = NicProfile(
    formula_id=formula.id,
    slug=slug,
    name=nic_profile.name,
    is_pre_mix=nic_profile.is_pre_mix,
    is_old_mix=nic_profile.is_old_mix,
    nic_base_nic_str=nic_profile.nic_base_nic_str,
    target_nic_str=nic_profile.target_nic_str,
    target_vg=nic_profile.target_vg,
    target_pg=nic_profile.target_pg,
  )

  db.add(nic_profile)
  db.commit()
  db.refresh(nic_profile)
  
  return NicProfileCreatePayload(
    nic_profile=NicProfileType.from_model(nic_profile),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def delete_nic_profile(db: Session, identifier: "NicProfileIdentifierInput") -> NicProfileDeletePayload:
  nic_profile = get_nic_profile(db=db, identifier=identifier)

  if not nic_profile:
    return NicProfileDeletePayload(
      deleted_slug=None,
      deleted_full_name=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Nic profile {identifier.slug} not found."
      )
    )
    
  slug = nic_profile.slug
  full_name = nic_profile.full_name

  db.delete(nic_profile)
  db.commit()

  return NicProfileDeletePayload(
    deleted_slug=slug,
    deleted_full_name=full_name,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None
    )
  )

def remove_nic_profile_flavoring(db: Session, identifier: "NicProfileFlavoringIdentifierInput") -> NicProfileFlavoringRemovePayload:
  flavoring = db.scalar(select(Flavoring).where(identifier.query_condition))
  
  if not flavoring:
    return NicProfileFlavoringRemovePayload(
      removed_slug=None,
      removed_name=None,
      removed_ratio=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message="Flavoring not found."
      )
    )
  
  slug = flavoring.slug
  name = flavoring.name
  ratio = flavoring.ratio
  
  db.delete(flavoring)
  db.commit()
  
  return NicProfileFlavoringRemovePayload(
    removed_slug=slug,
    removed_name=name,
    removed_ratio=ratio,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def remove_nic_profile_nic_base(db: Session, identifier: "NicProfileNicBaseIdentifierInput") -> NicProfileNicBaseRemovePayload:
  nic_base = db.scalar(select(NicBase).where(identifier.query_condition))
  
  if not nic_base:
    return NicProfileNicBaseRemovePayload(
      removed_code=None,
      removed_name=None,
      removed_ratio=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message="NicBase not found."
      )
    )
  
  code = nic_base.code
  name = nic_base.name
  ratio = nic_base.ratio
  
  db.delete(nic_base)
  db.commit()
  
  return NicProfileNicBaseRemovePayload(
    removed_code=code,
    removed_name=name,
    removed_ratio=ratio,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def update_nic_profile(db: Session, identifier: "NicProfileIdentifierInput", input: "NicProfileUpdateInput") -> NicProfileUpdatePayload:
  nic_profile = get_nic_profile(db=db, identifier=identifier)

  if not nic_profile:
    return NicProfileUpdatePayload(
      nic_profile=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Nic profile not found."
      )
    )

  updated_columns = []
  
  for attr, value in vars(input).items():
    current = getattr(nic_profile, attr, None)
    
    if value is strawberry.UNSET:
      continue
    if isinstance(value, Enum):
      value = value.name
      current = current.name
      
    if value != current:
      setattr(nic_profile, attr, value)
      db.flush()
      updated_columns.append(f"{attr}")
  
  if len(updated_columns) == 0:
    message = "Nothing to update"
  else:
    db.commit()
    db.refresh(nic_profile)
    message = f"Updated {", ".join(updated_columns)}"
  
  db.commit()
  db.refresh(nic_profile)
  
  return NicProfileUpdatePayload(
    nic_profile=NicProfileType.from_model(nic_profile),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=message
    )
  )