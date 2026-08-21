
from sqlalchemy.orm import Session
from sqlalchemy import select

import models

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