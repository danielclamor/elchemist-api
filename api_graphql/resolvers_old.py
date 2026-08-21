from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
import models

from api_graphql.resolvers.utils import make_slug

from api_graphql.types.enums import FeedbackStatus
from api_graphql.types.feedback import Feedback
from api_graphql.types.flavoring import FlavoringOptionCreateInput
from api_graphql.types.nic_base import NicBaseOptionCreateInput
from api_graphql.types.nic_profile import (
  NicProfileType,
  NicProfileCreatePayload,
  NicProfileDeletePayload,
  NicProfileUpdatePayload,
  NicProfileAddFlavoringPayload,
  NicProfileAddNicBasePayload,
)

if TYPE_CHECKING:
  from api_graphql.types.nic_profile import (
    NicProfileCreateInput,
    NicProfileDeleteInput,
    NicProfileUpdateIdentifier,
    NicProfileUpdateInput,
    NicProfileAddFlavoringInput,
    NicProfileAddNicBaseInput,
  )

# Query resolvers
def get_all_brands(db: Session) -> list[str]:
  return list(
    db.scalars(
      select(models.Formula.brand)
      .union(
        select(models.Eliquid.brand)
      )
    )
    .all()
  )

def get_all_eliquids(db: Session) -> list[models.Eliquid]:
  return (
    db.scalars(select(models.Eliquid)).all()
  )

def get_all_flavoring_options(db: Session) -> list[models.FlavoringOption]:
  return (
    db.scalars(select(models.FlavoringOption)).all()
  )

def get_all_nic_base_options(db: Session) -> list[models.NicBaseOption]:
  return (
    db.scalars(select(models.NicBaseOption)).all()
  )

def get_all_nic_profiles(db: Session) -> list[models.NicProfile]:
  return (
    db.scalars(select(models.NicProfile)).all()
  )

def get_eliquid(db: Session, eliquid_upc: str) -> models.Eliquid:
  return (
    db.scalar(select(models.Eliquid).where(models.Eliquid.upc == eliquid_upc))
  )

def get_flavoring_option(db: Session, flavoring_option_slug: str) -> models.FlavoringOption:
  return (
    db.scalar(select(models.FlavoringOption).where(models.FlavoringOption.slug == flavoring_option_slug))
  )

def get_nic_base_option(db: Session, nic_base_option_code: str) -> models.NicBaseOption:
  return (
    db.scalar(select(models.NicBaseOption).where(models.NicBaseOption.code == nic_base_option_code))
  )

def get_nic_profile(db: Session, nic_profile_slug: str) -> models.NicProfile:
  return (
    db.scalar(select(models.NicProfile).where(models.NicProfile.slug == nic_profile_slug))
  )


# Mutation resolvers
def add_nic_profile_flavoring(db: Session, nic_profile: models.NicProfile, flavoring: "NicProfileAddFlavoringInput") -> NicProfileAddFlavoringPayload:
  flavoring_option_slug = make_slug(flavoring.flavoring_option_name)
  existing_flavoring_option = get_flavoring_option(db=db, flavoring_option_slug=flavoring_option_slug)
  if not existing_flavoring_option:
    if flavoring.flavoring_option_is_vg is None:
      feedback = Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"No flavoring option {flavoring_option_slug} found. Can't create flavoring option {flavoring_option_slug} without isVg"
      )
      return NicProfileAddFlavoringPayload(
        nic_profile=NicProfileType.from_model(nic_profile),
        feedback=feedback,
      )

    existing_flavoring_option = create_flavoring_option(
      db=db,
      flavoring_option=FlavoringOptionCreateInput(
        name=flavoring.flavoring_option_name,
        is_vg=flavoring.flavoring_option_is_vg
      )
    )

  existing_flavoring = db.scalar(select(models.Flavoring).where(models.Flavoring.flavoring_option_id == existing_flavoring_option.id, models.Flavoring.nic_profile_id == nic_profile.id))
  if existing_flavoring:
    return NicProfileAddFlavoringPayload(
      nic_profile=NicProfileType.from_model(nic_profile),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Flavoring {existing_flavoring_option.name} is already connected"
      )
    )

  flavoring = models.Flavoring(
    nic_profile_id=nic_profile.id,
    flavoring_option_id=existing_flavoring_option.id,
    ratio=flavoring.ratio
  )

  db.add(flavoring)
  db.commit()
  db.refresh(flavoring)
  return NicProfileAddFlavoringPayload(
    nic_profile=NicProfileType.from_model(nic_profile),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=f"Flavoring {existing_flavoring_option.name} added to {nic_profile.full_name}"
    )
  )

def add_nic_profile_nic_base(db: Session, nic_profile: models.NicProfile, nic_base: "NicProfileAddNicBaseInput") -> NicProfileAddNicBasePayload:
  existing_nic_base_option = get_nic_base_option(db=db, nic_base_option_code=nic_base.nic_base_option_code)
  if not existing_nic_base_option:
    feedback_message_part = ""
    if nic_base.nic_base_option_name is None:
      feedback_message_part = "nicBaseOptionName"
    if nic_base.nic_base_option_is_vg is None:
      if feedback_message_part:
        feedback_message_part = f"{feedback_message_part} and "
      feedback_message_part = f"{feedback_message_part}isVg"

    if feedback_message_part:
      if nic_base.nic_base_option_name:
        nic_base_option_name = f"{nic_base.nic_base_option_name} "
      elif nic_base.nic_base_option_name is None:
        nic_base_option_name = ""

      feedback = Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"No nic base option {nic_base_option_name}({nic_base.nic_base_option_code}) found. Can't create nic base option {nic_base_option_name}({nic_base.nic_base_option_code}) without {feedback_message_part}"
      )

      return NicProfileAddNicBasePayload(
        nic_profile=NicProfileType.from_model(nic_profile),
        feedback=feedback,
      )

    existing_nic_base_option = create_nic_base_option(
      db=db,
      nic_base_option=NicBaseOptionCreateInput(
        code=nic_base.nic_base_option_code,
        name=nic_base.nic_base_option_name,
        is_vg=nic_base.nic_base_option_is_vg
      )
    )

  existing_nic_base = db.scalar(select(models.NicBase).where(models.NicBase.nic_base_option_id == existing_nic_base_option.id, models.NicBase.nic_profile_id == nic_profile.id))
  if existing_nic_base:
    return NicProfileAddNicBasePayload(
      nic_profile=NicProfileType.from_model(nic_profile),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Nic base {existing_nic_base_option.name} ({existing_nic_base_option.code}) is already connected"
      )
    )

  nic_base = models.NicBase(
    nic_profile_id=nic_profile.id,
    nic_base_option_id=existing_nic_base_option.id,
    ratio=nic_base.ratio,
  )

  db.add(nic_base)
  db.commit()
  db.refresh(nic_base)
  return NicProfileAddNicBasePayload(
    nic_profile=NicProfileType.from_model(nic_profile),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=f"Nic base {existing_nic_base_option.name} ({existing_nic_base_option.code}) added to {nic_profile.full_name}"
    )
  )

def bulk_add_nic_profile_flavorings(db: Session, nic_profile_slug: str, flavorings: "list[NicProfileAddFlavoringInput]") -> NicProfileAddFlavoringPayload:
  nic_profile = db.scalar(select(models.NicProfile).where(models.NicProfile.slug == nic_profile_slug))
  if not nic_profile:
    return NicProfileAddFlavoringPayload(
      nic_profile=None,
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Nic profile {nic_profile_slug} not found",
      )
    )

  for flavoring in flavorings:
    add_nic_profile_flavoring(db=db, nic_profile=nic_profile, flavoring=flavoring)

  return NicProfileAddFlavoringPayload(
    nic_profile=NicProfileType.from_model(nic_profile),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=f"Flavorings added to {nic_profile.full_name}"
    )
  )

def bulk_add_nic_profile_nic_bases(db: Session, nic_profile_slug: str, nic_bases: "list[NicProfileAddNicBaseInput]") -> NicProfileAddNicBasePayload:
  nic_profile = db.scalar(select(models.NicProfile).where(models.NicProfile.slug == nic_profile_slug))
  if not nic_profile:
    return NicProfileAddNicBasePayload(
      nic_profile=None,
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Nic profile {nic_profile_slug} not found",
      )
    )

  for nic_base in nic_bases:
    add_nic_profile_nic_base(db=db, nic_profile=nic_profile, nic_base=nic_base)

  return NicProfileAddNicBasePayload(
    nic_profile=NicProfileType.from_model(nic_profile),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=f"Nic bases added to {nic_profile.full_name}"
    )
  )

def create_nic_base_option(db: Session, nic_base_option: NicBaseOptionCreateInput) -> models.NicBaseOption:
  nic_base_option = models.NicBaseOption(
    code=nic_base_option.code,
    name=nic_base_option.name,
    is_vg=nic_base_option.is_vg,
  )

  db.add(nic_base_option)
  db.commit()
  db.refresh(nic_base_option)
  return nic_base_option

def create_flavoring_option(db: Session, flavoring_option: FlavoringOptionCreateInput) -> models.FlavoringOption:
  flavoring_option_slug = make_slug(flavoring_option.name)

  flavoring_option = models.FlavoringOption(
    slug=flavoring_option_slug,
    name=flavoring_option.name,
    is_vg=flavoring_option.is_vg,
  )

  db.add(flavoring_option)
  db.commit()
  db.refresh(flavoring_option)
  return flavoring_option

def create_nic_profile(db: Session, formula_slug: str, nic_profile: "NicProfileCreateInput") -> NicProfileCreatePayload:
  formula = db.scalar(select(models.Formula).where(models.Formula.slug == formula_slug))
  if not formula:
    return NicProfileCreatePayload(
      nic_profile=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"Formula {formula_slug} not found",
      )
    )

  suffix = " - Old Mix" if nic_profile.is_old_mix else ""
  full_name = f"{formula.name} - {nic_profile.name}{suffix}"
  slug = make_slug(full_name)

  existing = db.scalar(select(models.NicProfile).where(models.NicProfile.slug == slug,
                                                       models.NicProfile.formula_id == formula.id))
  if existing:
    return NicProfileCreatePayload(
      nic_profile=NicProfileType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Nic Profile {slug} already exists",
      )
    )

  nic_profile = models.NicProfile(
    formula_id=formula.id,
    slug=slug,
    full_name=full_name,
    name=nic_profile.name,
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

def delete_nic_profile(db: Session, input: "NicProfileDeleteInput") -> NicProfileDeletePayload:
  nic_profile = get_nic_profile(
    db=db,
    nic_profile_slug=input.slug
  )

  if not nic_profile:
    return NicProfileDeletePayload(
      deleted_slug=None,
      deleted_full_name=None,
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Nic profile {input.slug} not found."
      )
    )

  db.delete(nic_profile)
  db.commit()

  return NicProfileDeletePayload(
    deleted_slug=input.slug,
    deleted_full_name=nic_profile.full_name,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None
    )
  )

def update_nic_profile(db: Session, identifier: "NicProfileUpdateIdentifier", nic_profile: "NicProfileUpdateInput") -> NicProfileUpdatePayload:
  nic_profile_model = get_nic_profile(
    db=db,
    nic_profile_slug=identifier.slug
  )

  if not nic_profile_model:
    return NicProfileUpdatePayload(
      nic_profile=None,
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message=f"Nic profile {identifier.slug} not found."
      )
    )

  if nic_profile.slug:
    nic_profile_model.slug = nic_profile.slug

  if nic_profile.name:
    nic_profile_model.name = nic_profile.name

  if nic_profile.is_old_mix is not None:
    nic_profile_model.is_old_mix = nic_profile.is_old_mix

  if nic_profile.nic_base_nic_str is not None:
    nic_profile_model.nic_base_nic_str = nic_profile.nic_base_nic_str

  if nic_profile.target_nic_str is not None:
    nic_profile_model.target_nic_str = nic_profile.target_nic_str

  if nic_profile.target_vg is not None:
    nic_profile_model.target_vg = nic_profile.target_vg

  if nic_profile.target_pg is not None:
    nic_profile_model.target_pg = nic_profile.target_pg

  db.commit()
  db.refresh(nic_profile_model)
  return NicProfileUpdatePayload(
    nic_profile=NicProfileType.from_model(nic_profile_model),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None
    )
  )