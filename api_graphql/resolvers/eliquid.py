from sqlalchemy.orm import Session
from sqlalchemy import select

import models

# Queries
def get_all_eliquids(db: Session) -> list[models.Eliquid]:
  return (
    db.scalars(select(models.Eliquid)).all()
  )

def get_eliquid(db: Session, eliquid_upc: str) -> models.Eliquid:
  return (
    db.scalar(select(models.Eliquid).where(models.Eliquid.upc == eliquid_upc))
  )
