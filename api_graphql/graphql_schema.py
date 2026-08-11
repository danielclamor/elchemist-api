import strawberry
from typing import List, Optional
from database import SessionLocal
from api_graphql.graphql_types import FormulaType
from api_graphql.resolvers import formula_to_type, get_all_formulas
import models

@strawberry.type
class Query:
    @strawberry.field
    def formulas(self) -> List[FormulaType]:
        db = SessionLocal()
        try:
            return [formula_to_type(f) for f in get_all_formulas(db)]
        finally:
            db.close()

    @strawberry.field
    def formula(self, slug: str) -> Optional[FormulaType]:
        db = SessionLocal()
        try:
            f = db.query(models.Formula).filter(models.Formula.slug == slug).first()
            return formula_to_type(f) if f else None
        finally:
            db.close()

schema = strawberry.Schema(query=Query)