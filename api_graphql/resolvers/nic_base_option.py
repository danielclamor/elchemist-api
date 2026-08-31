from sqlalchemy.orm import Session
from sqlalchemy import select
import models

from api_graphql.types.nic_base_option import NicBaseOptionCreateInput

# Queries
def get_all_nic_base_options(db: Session) -> list[models.NicBaseOption]:
  return (
    db.scalars(select(models.NicBaseOption)).all()
  )
  
def get_nic_base_option(db: Session, nic_base_option_code: str) -> models.NicBaseOption:
  return (
    db.scalar(select(models.NicBaseOption).where(models.NicBaseOption.code == nic_base_option_code))
  )
  

# Mutations
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