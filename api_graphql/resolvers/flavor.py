import re
from typing import Optional

from sqlalchemy import case, func, select, or_
from sqlalchemy.orm import Session

from api_graphql.resolvers.utils import generate_slug
from models import ChillType, Flavor, NicType


def _generate_flavor_slug(name: str) -> str:
  # the name is "{Brand} {Nic Type} {Flavor Name}", so the slug is brand-nictype-name
  return generate_slug(name)

def _extract_chill_type(search_string: str) -> ChillType | None:
  NON_CHILLED_KEYWORDS = ["non-chilled", "nonchilled", "nonice", "non-ice"]
  CHILLED_KEYWORDS = ["chilled", "iced"]
    
  for kw in NON_CHILLED_KEYWORDS:
    if kw in search_string:
      return ChillType.NON_CHILLED
  
  for kw in CHILLED_KEYWORDS:
    if kw in search_string:
      return ChillType.CHILLED
  
  return None

def _extract_nic_type(search_string: str) -> NicType | None:
  SALT_KEYWORDS = ["salt"]
  FREEBASE_KEYWORDS = ["freebase", "fb"]
  
  has_salt = any(
    re.search(rf"\b{re.escape(kw)}\b", search_string, flags=re.IGNORECASE)
    for kw in SALT_KEYWORDS
  )
  
  has_freebase = any(
    re.search(rf"\b{re.escape(kw)}\b", search_string, flags=re.IGNORECASE)
    for kw in FREEBASE_KEYWORDS
  )

  if has_salt and has_freebase:
    return None
  if has_salt:
    return NicType.SALT
  if has_freebase:
    return NicType.FREEBASE

  return None

# def _filter_flavors(stmt, search_string:str=None):
#   if search_string is not None:
#     words = search_string.split()
#     match_score = sum(
#       case((Flavor.name.ilike(f"%{word}%"), 1), else_=0)
#       for word in words
#     )
#     print(match_score)
#     min_matches = int(len(words) * 0.8)
#     stmt = stmt.where(match_score >= min_matches).order_by(match_score.desc())
    
#     chill_type = _extract_chill_type(search_string)
    
#     if chill_type is not None:
#       stmt = stmt.where(Flavor.chill_type == chill_type)
      
#     nic_type = _extract_nic_type(search_string)
    
#     if nic_type is not None:
#       stmt = stmt.where(Flavor.nic_type == nic_type)
      
#   return stmt
def _filter_flavors(stmt, search_string:str=None):
  if search_string is not None:
    words = search_string.split()
    match_score = sum(
      case((Flavor.name.ilike(f"%{word}%"), 1), else_=0)
      for word in words
    )
    print(match_score)
    min_matches = int(len(words) * 1)
    stmt = stmt.where(match_score >= min_matches).order_by(match_score.desc())
      
  return stmt

def get_all_flavors(db: Session, search_string: Optional[str] = None) -> list[Flavor]:
  search_string = search_string.lower()
  stmt = select(Flavor)
  stmt = _filter_flavors(stmt, search_string).order_by(Flavor.name.desc())
  return db.scalars(stmt).unique().all()

def get_or_create_flavor(
  db: Session,
  brand: str,
  name: str,
  chill_type: ChillType,
  nic_type: NicType,
) -> Flavor:
  """Find the flavor with this identity (case-insensitive) or create it.

  Flushes but never commits, so the caller's transaction decides.
  """
  brand = " ".join(brand.split())
  name = " ".join(name.split())

  flavor = db.scalar(
    select(Flavor).where(
      func.lower(Flavor.brand) == brand.lower(),
      func.lower(Flavor.name) == name.lower(),
      Flavor.chill_type == chill_type,
      Flavor.nic_type == nic_type,
    )
  )

  if flavor is not None:
    return flavor

  base_slug = _generate_flavor_slug(name)
  slug, n = base_slug, 1
  while db.scalar(select(Flavor.id).where(Flavor.slug == slug)) is not None:
    n += 1
    slug = f"{base_slug}-{n}"

  flavor = Flavor(slug=slug, name=name, brand=brand, chill_type=chill_type, nic_type=nic_type)
  db.add(flavor)
  db.flush()

  return flavor