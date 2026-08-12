import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
  Boolean,
  DateTime,
  Enum,
  ForeignKey,
  Numeric,
  String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
  pass


class ChillType(enum.Enum):
  CHILLED = "chilled"
  NON_CHILLED = "non-chilled"


class NicType(enum.Enum):
  SALT = "salt"
  FREEBASE = "freebase"


class Formula(Base):
  __tablename__ = "formulas"

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
  name: Mapped[str] = mapped_column(String(255))
  brand: Mapped[str] = mapped_column(String(255))
  chill_type: Mapped[ChillType] = mapped_column(Enum(ChillType))
  nic_type: Mapped[NicType] = mapped_column(Enum(NicType))

  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
  updated_at: Mapped[datetime] = mapped_column(
    DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
  )

  nic_profiles: Mapped[list["NicProfile"]] = relationship(
    back_populates="formula", cascade="all, delete-orphan"
  )

  def __repr__(self) -> str:
    return f"<Formula {self.slug!r}>"


class NicProfile(Base):
  __tablename__ = "nic_profiles"

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  formula_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("formulas.id"))

  slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
  name: Mapped[str] = mapped_column(String(255))
  full_name: Mapped[str | None] = mapped_column(String, nullable=True)

  is_new_mix: Mapped[bool] = mapped_column(Boolean, default=False)

  target_nic_str: Mapped[float] = mapped_column(Numeric(6, 3))
  target_vg: Mapped[float] = mapped_column(Numeric(6, 3))
  target_pg: Mapped[float] = mapped_column(Numeric(6, 3))
  nic_base_nic_str: Mapped[float] = mapped_column(Numeric(6, 3))

  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
  updated_at: Mapped[datetime] = mapped_column(
    DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
  )

  formula: Mapped["Formula"] = relationship(back_populates="nic_profiles")

  nic_bases: Mapped[list["NicBase"]] = relationship(
    back_populates="nic_profile", cascade="all, delete-orphan"
  )
  flavorings: Mapped[list["Flavoring"]] = relationship(
    back_populates="nic_profile", cascade="all, delete-orphan"
  )

  def __repr__(self) -> str:
    return f"<NicProfile {self.slug!r}>"


class NicBaseOption(Base):
  __tablename__ = "nic_base_options"

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
  name: Mapped[str] = mapped_column(String(255))
  is_vg: Mapped[bool] = mapped_column(Boolean)

  def __repr__(self) -> str:
    return f"<NicBaseOption {self.code!r}>"


class NicBase(Base):
  __tablename__ = "nic_bases"

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  nic_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nic_profiles.id"))
  nic_base_option_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("nic_base_options.id")
  )
  ratio: Mapped[float] = mapped_column(Numeric(6, 4))

  nic_profile: Mapped["NicProfile"] = relationship(back_populates="nic_bases")
  nic_base_option: Mapped["NicBaseOption"] = relationship()

  @property
  def code(self) -> str:
    return self.nic_base_option.code

  @property
  def name(self) -> str:
    return self.nic_base_option.name

  @property
  def is_vg(self) -> bool:
    return self.nic_base_option.is_vg

  @property
  def percentage(self) -> float:
    return float(self.ratio) * 100

  def __repr__(self) -> str:
    return f"<NicBase {self.code!r} ratio={self.ratio}>"

class FlavoringOption(Base):
  __tablename__ = "flavoring_options"
  
  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
  name: Mapped[str] = mapped_column(String(255))
  is_vg: Mapped[bool] = mapped_column(Boolean)
  
  def __repr__(self) -> str:
    return f"<FlavoringOption {self.slug!r}>"

class Flavoring(Base):
  __tablename__ = "flavorings"

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  nic_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nic_profiles.id"))
  flavoring_option_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("flavoring_options.id")
  )
  ratio: Mapped[float] = mapped_column(Numeric(6, 4))
  
  flavoring_option: Mapped["FlavoringOption"] = relationship()

  nic_profile: Mapped["NicProfile"] = relationship(back_populates="flavorings")

  @property
  def percentage(self) -> float:
    return float(self.ratio) * 100

  @property
  def name(self) -> str:
    return self.flavoring_option.name
  
  @property
  def is_vg(self) -> Boolean:
    return self.flavoring_option.is_vg

  def __repr__(self) -> str:
    return f"<Flavoring {self.name!r} ratio={self.ratio} is_vg={self.is_vg}>"