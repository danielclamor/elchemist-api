from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api_graphql.resolvers.utils import generate_slug
from models import ChillType, Flavor, NicType


def _generate_flavor_slug(name: str) -> str:
  # the name is "{Brand} {Nic Type} {Flavor Name}", so the slug is brand-nictype-name
  return generate_slug(name)


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