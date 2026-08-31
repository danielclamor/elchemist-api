from sqlalchemy.orm import Session
from sqlalchemy import select
from models import NicBaseOption

from api_graphql.types.feedback import Feedback, FeedbackStatus

from api_graphql.types.nic_base_option import (
  NicBaseOptionType,
  NicBaseOptionCreatePayload,
  NicBaseOptionsBulkCreatePayload,
  NicBaseOptionDeletePayload,
  NicBaseOptionsBulkDeletePayload,
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from api_graphql.types.nic_base_option import (
    NicBaseOptionIdentifierInput,
    NicBaseOptionCreateInput
  )

# Queries
def get_all_nic_base_options(db: Session) -> list[NicBaseOption]:
  return (
    db.scalars(select(NicBaseOption)).all()
  )
  
def get_nic_base_option(db: Session, identifier: "NicBaseOptionIdentifierInput") -> NicBaseOption:
  return (
    db.scalar(select(NicBaseOption).where(identifier.query_condition))
  )
  

# Mutations
def create_nic_base_option(db: Session, input: "NicBaseOptionCreateInput") -> NicBaseOptionCreatePayload:
  existing = db.scalar(select(NicBaseOption).where(NicBaseOption.code == input.code))
  
  if existing:
    return NicBaseOptionCreatePayload(
      nic_base_option=NicBaseOptionType.from_model(existing),
      feedback=Feedback(
        status=FeedbackStatus.SUCCESS,
        message=f"NicBaseOption {existing.code} already exists."
      )
    )
  
  nic_base_option = NicBaseOption(
    code=input.code,
    name=input.name,
    is_vg=input.is_vg,
  )

  db.add(nic_base_option)
  db.commit()
  db.refresh(nic_base_option)
  
  return NicBaseOptionCreatePayload(
    nic_base_option=NicBaseOptionType.from_model(nic_base_option),
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def bulk_create_nic_base_options(db: Session, inputs: list["NicBaseOptionCreateInput"]) -> NicBaseOptionsBulkCreatePayload:
  if len(inputs) == 0:
    return NicBaseOptionsBulkCreatePayload(
      nic_base_options=[],
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message="Nothing to add.",
      )
    )
  
  nic_base_options = []
  
  for input in inputs:
    nic_base_options.append(create_nic_base_option(db=db, input=input))
    
  return NicBaseOptionsBulkCreatePayload(
    nic_base_option=nic_base_options,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def delete_nic_base_option(db: Session, identifier: "NicBaseOptionIdentifierInput") -> NicBaseOptionDeletePayload:
  nic_base_option = get_nic_base_option(db=db, identifier=identifier)
  
  if not nic_base_option:
    return NicBaseOptionDeletePayload(
      deleted_code=None,
      deleted_name=None,
      feedback=Feedback(
        status=FeedbackStatus.FAILED,
        message=f"NicBaseOption {identifier.provided[1]} not found."
      )
    )
  
  db.delete(nic_base_option)
  db.commit()
  
  return NicBaseOptionDeletePayload(
    deleted_code=nic_base_option.code,
    deleted_name=nic_base_option.name,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )

def bulk_delete_flavoring_options(db: Session, identifiers: list["NicBaseOptionIdentifierInput"]) -> NicBaseOptionsBulkDeletePayload:
  if len(identifiers) == 0:
    return NicBaseOptionsBulkDeletePayload(
      deleted=[],
      feedback=Feedback(
        status=FeedbackStatus.CANCELLED,
        message="Nothing to delete.",
      )
    )
  
  deleted = []
  
  for identifier in identifiers:
    deleted.append(delete_nic_base_option(db=db, identifier=identifier))
  
  return NicBaseOptionsBulkDeletePayload(
    deleted=deleted,
    feedback=Feedback(
      status=FeedbackStatus.SUCCESS,
      message=None,
    )
  )