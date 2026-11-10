from __future__ import annotations
from enum import Enum
import uuid

from graphql import GraphQLError
from sqlalchemy.orm import Session
from sqlalchemy import and_, delete, select
import strawberry

from .utils import generate_slug

from models import (
  Formula,
  Flavoring,
  NicBase,
)

from api_graphql.resolvers.flavoring_option import (
  get_flavoring_option,
)

from api_graphql.resolvers.nic_base_option import (
  get_nic_base_option,
)

from api_graphql.types.feedback import Feedback, FeedbackStatusEnum

from api_graphql.types.formula import (
  FormulaType,
  FormulaCreatePayload,
  FormulaDeletePayload,
  FormulaUpdatePayload,
  FormulaFlavoringType,
  FormulaFlavoringAddPayload,
  FormulaFlavoringsBulkAddPayload,
  FormulaFlavoringsBulkRemovePayload,
  FormulaFlavoringRemovePayload,
  FormulaNicBaseType,
  FormulaNicBaseAddPayload,
  FormulaNicBasesBulkAddPayload,
  FormulaNicBasesBulkRemovePayload,
  FormulaNicBaseRemovePayload,
  FormulaNicBasesSetPayload,
)

from typing import TYPE_CHECKING
if TYPE_CHECKING: 
  from api_graphql.types.formula import (
    FormulaIdentifierInput,
    FormulaCreateInput,
    FormulaUpdateInput,
    FormulaFlavoringIdentifierInput,
    FormulaFlavoringInput,
    FormulaNicBaseIdentifierInput,
    FormulaNicBaseInput,
  )
  
  
# Queries
def get_all_formulas(db: Session) -> list[Formula]:
  return (
    db.scalars(select(Formula))
    .unique()
    .all()
  )

def get_formula(db: Session, identifier: "FormulaIdentifierInput") -> Formula | None:
  return (
    db.scalar(select(Formula).where(identifier.query_condition))
  )
  
  
# Mutations
def add_formula_flavoring(db: Session, id: uuid.UUID, input: "FormulaFlavoringInput") -> FormulaFlavoringAddPayload:
  flavoring_option = get_flavoring_option(db=db, identifier=input.flavoring_option_identifier)
  
  if flavoring_option is None:
    return FormulaFlavoringAddPayload(
      formula_flavoring=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"FlavoringOption {input.flavoring_option_identifier.provided[1]} not found."
      )
    )
    
  existing = db.scalar(
    select(Flavoring).where(
      and_(
        Flavoring.flavoring_option_id == flavoring_option.id,
        Flavoring.formula_id == id,
      )
    )
  )
  
  if existing is not None:
    return FormulaFlavoringAddPayload(
      formula_flavoring=FormulaFlavoringType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"Flavoring {existing.name} is already connected with ratio {existing.ratio}"
      )
    )

  flavoring = Flavoring(
    formula_id=id,
    flavoring_option_id=flavoring_option.id,
    ratio=input.ratio,
  )

  db.add(flavoring)
  db.commit()
  db.refresh(flavoring)
  
  return FormulaFlavoringAddPayload(
    formula_flavoring=FormulaFlavoringType.from_model(flavoring),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def add_formula_nic_base(db: Session, id: uuid.UUID, input: "FormulaNicBaseInput") -> FormulaNicBaseAddPayload:
  nic_base_option = get_nic_base_option(db=db, identifier=input.nic_base_option_identifier)
  
  if nic_base_option is None:
    return FormulaNicBaseAddPayload(
      formula_nic_base=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"NicBaseOption {input.nic_base_option_identifier.provided[1]} not found."
      )
    )
  
  existing = db.scalar(
    select(NicBase).where(
      and_(
        NicBase.nic_base_option_id == nic_base_option.id,
        NicBase.formula_id == id,
      )
    )
  )
  
  if existing is not None:
    return FormulaNicBaseAddPayload(
      formula_nic_base=FormulaNicBaseType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"NicBase {existing.name} is already connected with ratio {existing.ratio}"
      )
    )
  
  nic_base = NicBase(
    formula_id=id,
    nic_base_option_id=nic_base_option.id,
    ratio=input.ratio,
  )
  
  db.add(nic_base)
  db.commit()
  db.refresh(nic_base)
  
  return FormulaNicBaseAddPayload(
    formula_nic_base=FormulaNicBaseType.from_model(nic_base),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def bulk_add_formula_flavorings(db: Session, identifier: "FormulaIdentifierInput", inputs: list["FormulaFlavoringInput"]) -> FormulaFlavoringsBulkAddPayload:
  formula = get_formula(db=db, identifier=identifier)
  
  if formula is None:
    return FormulaFlavoringsBulkAddPayload(
      formula_flavorings=[],
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Formula {identifier.provided[1]} not found."
      )
    )
  
  if len(inputs) == 0:
    return FormulaFlavoringsBulkAddPayload(
      formula_flavorings=[],
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message="Nothing to add"
      )
    )
  
  flavorings = []
  
  for input in inputs:
    flavorings.append(add_formula_flavoring(db=db, id=formula.id, input=input))
    
  return FormulaFlavoringsBulkAddPayload(
    formula_flavorings=flavorings,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def bulk_add_formula_nic_bases(db: Session, identifier: "FormulaIdentifierInput", inputs: list["FormulaNicBaseInput"]) -> FormulaNicBasesBulkAddPayload:
  formula = get_formula(db=db, identifier=identifier)
  
  if formula is None:
    return FormulaNicBasesBulkAddPayload(
      formula_nic_bases=[],
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Formula {identifier.provided[1]} not found."
      )
    )
    
  if len(inputs) == 0:
    return FormulaNicBasesBulkAddPayload(
      formula_nic_bases=[],
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message="Nothing to add"
      )
    )
  
  nic_bases = []
  
  for input in inputs:
    nic_bases.append(add_formula_nic_base(db=db, id=formula.id, input=input))
    
  return FormulaNicBasesBulkAddPayload(
    formula_nic_bases=nic_bases,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def bulk_remove_formula_flavorings(db: Session, identifiers: list[FormulaFlavoringIdentifierInput]) -> FormulaFlavoringsBulkRemovePayload:
  removed = []
  
  if len(identifiers) == 0:
    return FormulaFlavoringsBulkRemovePayload(
      formula_flavorings=[],
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message="Nothing to remove.",
      )
    )
  
  for identifier in identifiers:
    removed.append(remove_formula_flavoring(db=db, identifier=identifier))
    
  return FormulaFlavoringsBulkRemovePayload(
    formula_flavorings=removed,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def bulk_remove_formula_nic_bases(db: Session, identifiers: list[FormulaNicBaseIdentifierInput]) -> FormulaNicBasesBulkRemovePayload:
  removed = []
  
  if len(identifiers) == 0:
    return FormulaNicBasesBulkRemovePayload(
      formula_nic_bases=[],
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message="Nothing to remove.",
      )
    )
  
  for identifier in identifiers:
    removed.append(remove_formula_nic_base(db=db, identifier=identifier))
    
  return FormulaNicBasesBulkRemovePayload(
    formula_nic_bases=removed,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )
  
def create_formula(db: Session, formula: "FormulaCreateInput") -> FormulaCreatePayload:
  slug = generate_slug(formula.name)

  existing = db.scalar(
    select(Formula).where(
      and_(
        Formula.slug == slug,
      )
    )
  )
  
  if existing is not None:
    return FormulaCreatePayload(
      formula=FormulaType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message=f"Formula {slug} already exists",
      )
    )

  formula = Formula(
    slug=slug,
    name=formula.name,
    is_pre_mix=formula.is_pre_mix,
    is_old_mix=formula.is_old_mix,
    nic_base_nic_str=formula.nic_base_nic_str,
    target_nic_str=formula.target_nic_str,
    target_vg=formula.target_vg,
    target_pg=formula.target_pg,
  )

  db.add(formula)
  db.commit()
  db.refresh(formula)
  
  return FormulaCreatePayload(
    formula=FormulaType.from_model(formula),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def delete_formula(db: Session, identifier: "FormulaIdentifierInput") -> FormulaDeletePayload:
  formula = get_formula(db=db, identifier=identifier)

  if formula is None:
    return FormulaDeletePayload(
      deleted_slug=None,
      deleted_full_name=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Formula {identifier.slug} not found."
      )
    )
    
  slug = formula.slug
  full_name = formula.full_name

  db.delete(formula)
  db.commit()

  return FormulaDeletePayload(
    deleted_slug=slug,
    deleted_full_name=full_name,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None
    )
  )

def remove_formula_flavoring(db: Session, identifier: "FormulaFlavoringIdentifierInput") -> FormulaFlavoringRemovePayload:
  flavoring = db.scalar(select(Flavoring).where(identifier.query_condition))
  
  if flavoring is None:
    return FormulaFlavoringRemovePayload(
      removed_slug=None,
      removed_name=None,
      removed_ratio=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="Flavoring not found."
      )
    )
  
  slug = flavoring.slug
  name = flavoring.name
  ratio = flavoring.ratio
  
  db.delete(flavoring)
  db.commit()
  
  return FormulaFlavoringRemovePayload(
    removed_slug=slug,
    removed_name=name,
    removed_ratio=ratio,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def remove_formula_nic_base(db: Session, identifier: "FormulaNicBaseIdentifierInput") -> FormulaNicBaseRemovePayload:
  nic_base = db.scalar(select(NicBase).where(identifier.query_condition))
  
  if nic_base is None:
    return FormulaNicBaseRemovePayload(
      removed_code=None,
      removed_name=None,
      removed_ratio=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message="NicBase not found."
      )
    )
  
  code = nic_base.code
  name = nic_base.name
  ratio = nic_base.ratio
  
  db.delete(nic_base)
  db.commit()
  
  return FormulaNicBaseRemovePayload(
    removed_code=code,
    removed_name=name,
    removed_ratio=ratio,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def set_formula_nic_bases(db: Session, identifier: "FormulaIdentifierInput", inputs: list["FormulaNicBaseInput"]) -> FormulaNicBasesSetPayload:
  if sum(i.ratio for i in inputs) != 1:
    raise GraphQLError(
      "sum of nicBases must be 1",
      extensions={"code": "INPUT_ERROR", "inputObjectType": "[FormulaNicBaseInput]"}
    )
  
  formula = get_formula(db=db, identifier=identifier)
  
  if formula is None:
    return FormulaNicBasesSetPayload(
      formula_nic_bases=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Formula {identifier.provided[1]} not found."
      )
    )
  
  if len(inputs) == 0:
    return FormulaNicBasesSetPayload(
      formula_nic_bases=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.CANCELLED,
        message="Nothing to set"
      )
    )
  
  nic_bases: list[NicBase] = []
  
  for input in inputs:
    nic_base_option = get_nic_base_option(db=db, identifier=input.nic_base_option_identifier)
    
    if nic_base_option is None:
      return FormulaNicBasesSetPayload(
        formula_nic_bases=None,
        feedback=Feedback(
          status=FeedbackStatusEnum.FAILED,
          message=f"NicBaseOption {input.nic_base_option_identifier.provided[1]} not found."
        )
      )
    
    nic_bases.append(
      NicBase(
        formula_id=formula.id,
        nic_base_option_id=nic_base_option.id,
        ratio=input.ratio,
      )
    )
  
  db.execute(delete(NicBase).where(NicBase.formula_id == formula.id))
  db.flush()
  
  nic_base_types: list[FormulaNicBaseType] = []
  for nic_base in nic_bases:
    db.add(nic_base)
    db.flush()
    nic_base_types.append(FormulaNicBaseType.from_model(nic_base))
  
  db.commit()
  db.refresh(formula)
  
  return FormulaNicBasesSetPayload(
    formula_nic_bases=nic_base_types,
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=None,
    )
  )

def update_formula(db: Session, identifier: "FormulaIdentifierInput", input: "FormulaUpdateInput") -> FormulaUpdatePayload:
  formula = get_formula(db=db, identifier=identifier)

  if formula is None:
    return FormulaUpdatePayload(
      formula=None,
      feedback=Feedback(
        status=FeedbackStatusEnum.FAILED,
        message=f"Formula not found."
      )
    )

  updated_columns = []
  
  for attr, value in vars(input).items():
    current = getattr(formula, attr, None)
    
    if value is strawberry.UNSET:
      continue
    if isinstance(value, Enum):
      value = value.name
      current = current.name if current else None
      
    if value != current:
      setattr(formula, attr, value)
      db.flush()
      updated_columns.append(attr)
  
  if len(updated_columns) == 0:
    message = "Nothing to update"
  else:
    db.commit()
    db.refresh(formula)
    message = f"Updated {', '.join(updated_columns)}"
  
  db.commit()
  db.refresh(formula)
  
  return FormulaUpdatePayload(
    formula=FormulaType.from_model(formula),
    feedback=Feedback(
      status=FeedbackStatusEnum.SUCCESS,
      message=message
    )
  )