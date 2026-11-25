"""add flavors table; move brand/chill_type/nic_type off formulas and eliquids

Revision ID: f1c9a3e7b258
Revises: d8b5f2a7c914
Create Date: 2026-11-24 17:00:00.000000

A flavor is (brand, flavor name, chill type, nic type). Formulas and eliquids
now point at one through flavor_id and no longer carry brand / chill_type /
nic_type themselves.

Backfill
  - Formula names are "{Brand} {Flavor Name} {Nic Type} {Nic Level}", so the
    flavor name is the formula name with only the trailing nic level (20mg /
    hit35) removed: "Slice Big Island (Iced) Salt 10mg" -> "Slice Big Island
    (Iced) Salt", "Black Jet Do More Freebase Old Mix 0mg" -> "Black Jet Do More
    Freebase Old Mix". Nothing else is touched.
  - Eliquid: if its formula has the same brand / chill type / nic type it
    shares that formula's flavor. Otherwise the trailing bottle size and nic
    level are removed from its description ("Slice Big Island (Iced) Salt 30ml
    10mg" -> "Slice Big Island (Iced) Salt") and the result is matched to an
    existing flavor with the same brand / chill / nic type (case-insensitive)
    or becomes a new flavor.
  - The flavor slug is the slug of the flavor name (brand, flavor and nic type
    are already in it), with -2, -3 ... added if two would collide.
  - Any row whose flavor name comes out empty stops the migration (nothing is
    changed: the whole migration is one transaction).

Hand-written: the data has to be converted before the old columns go.
"""
import re
import uuid
from typing import Optional, Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f1c9a3e7b258'
down_revision: Union[str, Sequence[str], None] = 'd8b5f2a7c914'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


chill_type = postgresql.ENUM('CHILLED', 'NON_CHILLED', name='chilltype', create_type=False)
nic_type = postgresql.ENUM('FREEBASE', 'SALT', name='nictype', create_type=False)

LEVEL = re.compile(r'\s*\b(?:\d+(?:\.\d+)?\s*mg|hit\s*\d+)\s*$', re.I)
SIZE = re.compile(r'\s*\b\d+(?:\.\d+)?\s*ml\s*$', re.I)
OLD_MIX = re.compile(r'\s*\bOld\s+Mix\s*$', re.I)


def clean_name(text: str, strip_size: bool, is_old_mix: Optional[bool] = None) -> str:
    """Remove the trailing nic level (and, for eliquid descriptions, bottle size)."""
    patterns = [LEVEL] + ([SIZE] if strip_size else []) + ([OLD_MIX] if is_old_mix else [])
    s = ' '.join((text or '').split())
    changed = True
    while changed and s:
        changed = False
        for p in patterns:
            new = p.sub('', s).strip()
            if new != s:
                s, changed = new, True
    return s


def slugify(text: str) -> str:
    return '-'.join(t for t in re.sub(r'[^a-zA-Z0-9]', ' ', text).split(' ') if t).lower()


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        'flavors',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('brand', sa.String(length=255), nullable=False),
        sa.Column('chill_type', chill_type, nullable=False),
        sa.Column('nic_type', nic_type, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('brand', 'name', 'chill_type', 'nic_type', name='uq_flavors_identity'),
    )
    op.create_index(op.f('ix_flavors_slug'), 'flavors', ['slug'], unique=True)
    op.create_index(op.f('ix_flavors_brand'), 'flavors', ['brand'], unique=False)

    op.add_column('formulas', sa.Column('flavor_id', sa.Uuid(), nullable=True))
    op.add_column('eliquids', sa.Column('flavor_id', sa.Uuid(), nullable=True))

    flavors = {}       # (brand_l, name_l, chill, nic) -> id
    slugs = set()
    problems = []

    def get_flavor(brand: str, name: str, chill: str, nic: str):
        brand = ' '.join(brand.split())
        key = (brand.lower(), name.lower(), chill, nic)
        if key in flavors:
            return flavors[key]
        base = slugify(name)
        slug, n = base, 1
        while slug in slugs:
            n += 1
            slug = f"{base}-{n}"
        slugs.add(slug)
        fid = uuid.uuid4()
        bind.execute(
            sa.text("INSERT INTO flavors (id, slug, name, brand, chill_type, nic_type) "
                    "VALUES (:id, :slug, :name, :brand, CAST(:chill AS chilltype), CAST(:nic AS nictype))"),
            dict(id=fid, slug=slug, name=name, brand=brand, chill=chill, nic=nic),
        )
        flavors[key] = fid
        return fid

    formulas = bind.execute(sa.text(
        "SELECT id, slug, name, brand, chill_type::text, nic_type::text, is_old_mix FROM formulas ORDER BY created_at, id"
    )).all()
    formula_flavor = {}   # formula id -> (flavor id, brand, chill, nic)
    for fid, slug, name, brand, chill, nic, is_old_mix in formulas:
        flavor_name = clean_name(name, strip_size=False, is_old_mix=is_old_mix)
        if not flavor_name:
            problems.append(f"formula {slug!r}: name {name!r} leaves no flavor name")
            continue
        flv = get_flavor(brand, flavor_name, chill, nic)
        formula_flavor[fid] = (flv, brand, chill, nic)
        bind.execute(sa.text("UPDATE formulas SET flavor_id = :f WHERE id = :id"), dict(f=flv, id=fid))

    eliquids = bind.execute(sa.text(
        "SELECT id, upc, description, brand, chill_type::text, nic_type::text, formula_id "
        "FROM eliquids ORDER BY created_at, id"
    )).all()
    for eid, upc, desc, brand, chill, nic, formula_id in eliquids:
        linked = formula_flavor.get(formula_id)
        if linked and linked[1:] == (brand, chill, nic):
            flv = linked[0]
        else:
            flavor_name = clean_name(desc, strip_size=True)
            if not flavor_name:
                problems.append(f"eliquid {upc!r}: description {desc!r} leaves no flavor name")
                continue
            flv = get_flavor(brand, flavor_name, chill, nic)
        bind.execute(sa.text("UPDATE eliquids SET flavor_id = :f WHERE id = :id"), dict(f=flv, id=eid))

    if problems:
        raise RuntimeError("Cannot derive a flavor name for:\n  " + "\n  ".join(problems))

    for table in ('formulas', 'eliquids'):
        op.alter_column(table, 'flavor_id', nullable=False)
        op.create_foreign_key(f'fk_{table}_flavor_id_flavors', table, 'flavors', ['flavor_id'], ['id'])
        op.create_index(op.f(f'ix_{table}_flavor_id'), table, ['flavor_id'], unique=False)
        op.drop_column(table, 'brand')
        op.drop_column(table, 'chill_type')
        op.drop_column(table, 'nic_type')


def downgrade() -> None:
    bind = op.get_bind()
    for table in ('formulas', 'eliquids'):
        op.add_column(table, sa.Column('brand', sa.String(length=255), nullable=True))
        op.add_column(table, sa.Column('chill_type', chill_type, nullable=True))
        op.add_column(table, sa.Column('nic_type', nic_type, nullable=True))
        bind.execute(sa.text(
            f"UPDATE {table} t SET brand = f.brand, chill_type = f.chill_type, nic_type = f.nic_type "
            f"FROM flavors f WHERE f.id = t.flavor_id"
        ))
        op.alter_column(table, 'brand', nullable=False)
        op.alter_column(table, 'chill_type', nullable=False)
        op.alter_column(table, 'nic_type', nullable=False)
        op.drop_index(op.f(f'ix_{table}_flavor_id'), table_name=table)
        op.drop_constraint(f'fk_{table}_flavor_id_flavors', table, type_='foreignkey')
        op.drop_column(table, 'flavor_id')

    op.drop_index(op.f('ix_flavors_brand'), table_name='flavors')
    op.drop_index(op.f('ix_flavors_slug'), table_name='flavors')
    op.drop_table('flavors')
