# import uuid

# from fastapi import Depends, FastAPI, HTTPException
# from sqlalchemy.orm import Session

# import models
# import schemas
# from database import get_db

# app = FastAPI(title="Elchemist API")


# # @app.get("/")
# # def root():
# #     return {"status": "ok"}


# # # --- Formulas ---


# # @app.get("/formulas", response_model=list[schemas.FormulaOut])
# # def list_formulas(db: Session = Depends(get_db)):
# #     return db.query(models.Formula).all()


# # @app.get("/formulas/{formula_id}", response_model=schemas.FormulaOut)
# # def get_formula(formula_id: uuid.UUID, db: Session = Depends(get_db)):
# #     formula = db.get(models.Formula, formula_id)
# #     if not formula:
# #         raise HTTPException(status_code=404, detail="Formula not found")
# #     return formula


# # @app.post("/formulas", response_model=schemas.FormulaOut, status_code=201)
# # def create_formula(payload: schemas.FormulaCreate, db: Session = Depends(get_db)):
# #     formula = models.Formula(**payload.model_dump())
# #     db.add(formula)
# #     db.commit()
# #     db.refresh(formula)
# #     return formula


# # # --- Nic base options (reference/lookup data) ---


# # @app.get("/nic-base-options", response_model=list[schemas.NicBaseOptionOut])
# # def list_nic_base_options(db: Session = Depends(get_db)):
# #     return db.query(models.NicBaseOption).all()


# # # --- Nic profiles (nested under a formula) ---


# # @app.post(
# #     "/formulas/{formula_id}/nic-profiles",
# #     response_model=schemas.NicProfileOut,
# #     status_code=201,
# # )
# # def create_nic_profile(
# #     formula_id: uuid.UUID,
# #     payload: schemas.NicProfileCreate,
# #     db: Session = Depends(get_db),
# # ):
# #     formula = db.get(models.Formula, formula_id)
# #     if not formula:
# #         raise HTTPException(status_code=404, detail="Formula not found")

# #     data = payload.model_dump(exclude={"nic_bases", "flavorings"})
# #     nic_profile = models.NicProfile(**data, formula_id=formula_id)

# #     for nb in payload.nic_bases:
# #         nic_profile.nic_bases.append(models.NicBase(**nb.model_dump()))

# #     for fl in payload.flavorings:
# #         nic_profile.flavorings.append(models.Flavoring(**fl.model_dump()))

# #     db.add(nic_profile)
# #     db.commit()
# #     db.refresh(nic_profile)
# #     return nic_profile

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from database import SessionLocal
from api_graphql.schema import schema

app = FastAPI(title="Elchemist API")

async def get_context():
  db = SessionLocal()
  try:
    yield {"db": db}
  finally:
    db.close()

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")
