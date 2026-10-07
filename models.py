import enum
import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
  Boolean,
  CheckConstraint,
  Date,
  DateTime,
  Enum,
  ForeignKey,
  Index,
  Integer,
  Numeric,
  String,
  UniqueConstraint,
  func,
  text,
)

from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
  pass


class BottleColor(enum.Enum):
  BLACK = "black"
  CLEAR = "clear"
  WHITE = "white"
  

bottle_color_enum = Enum(BottleColor, name="bottlecolor")


class ChillType(enum.Enum):
  CHILLED = "chilled"
  NON_CHILLED = "non-chilled"


chill_type_enum = Enum(ChillType, name="chilltype")


class NicType(enum.Enum):
  FREEBASE = "freebase"
  SALT = "salt"


nic_type_enum = Enum(NicType, name="nictype")


class BottleSize(enum.Enum):
  ML_30 = "30ml"
  ML_60 = "60ml"
  ML_120 = "120ml"


bottle_size_enum = Enum(BottleSize, name="bottlesize")


class NicLevel(enum.Enum):
  MG_0 = "0mg"
  MG_3 = "3mg"
  MG_5 = "5mg"
  MG_6 = "6mg"
  MG_10 = "10mg"
  MG_12 = "12mg"
  MG_15 = "15mg"
  MG_18 = "18mg"
  MG_20 = "20mg"
  HIT_35 = "hit35"
  HIT_50 = "hit50"


nic_level_enum = Enum(NicLevel, name="niclevel")


class Eliquid(Base):
  __tablename__ = "eliquids"

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  upc: Mapped[str] = mapped_column(String(12), unique=True, index=True)
  description: Mapped[str] = mapped_column(String(255))
  brand: Mapped[str] = mapped_column(String(255))
  chill_type: Mapped[ChillType] = mapped_column(chill_type_enum)
  nic_type: Mapped[NicType] = mapped_column(nic_type_enum)
  bottle_size: Mapped[BottleSize] = mapped_column(bottle_size_enum)
  nic_level: Mapped[NicLevel] = mapped_column(nic_level_enum)
  bottle_color: Mapped[BottleColor] = mapped_column(bottle_color_enum)
  nic_profile_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("nic_profiles.id", ondelete="SET NULL"), index=True)

  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )
  
  nic_profile: Mapped["NicProfile"] = relationship()
  
  production_orders: Mapped[list["ProductionOrder"]] = relationship(back_populates="eliquid")

  def __repr__(self) -> str:
    return f"<Eliquid {self.description!r}>"


class Formula(Base):
  __tablename__ = "formulas"

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
  name: Mapped[str] = mapped_column(String(255))
  brand: Mapped[str] = mapped_column(String(255))
  chill_type: Mapped[ChillType] = mapped_column(chill_type_enum)
  nic_type: Mapped[NicType] = mapped_column(nic_type_enum)
  
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )

  nic_profiles: Mapped[list["NicProfile"]] = relationship(
    back_populates="formula", cascade="all, delete-orphan"
  )

  def __repr__(self) -> str:
    return f"<Formula {self.slug!r}>"


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
  nic_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nic_profiles.id", ondelete="CASCADE"), index=True)
  flavoring_option_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("flavoring_options.id"), index=True)
  ratio: Mapped[float] = mapped_column(Numeric(7, 6))
  
  flavoring_option: Mapped["FlavoringOption"] = relationship()

  nic_profile: Mapped["NicProfile"] = relationship(back_populates="flavorings")

  @property
  def percentage(self) -> float:
    return float(self.ratio) * 100

  @property
  def slug(self) -> str:
    return self.flavoring_option.slug
  
  @property
  def name(self) -> str:
    return self.flavoring_option.name
  
  @property
  def is_vg(self) -> bool:
    return self.flavoring_option.is_vg

  def __repr__(self) -> str:
    return f"<Flavoring {self.name!r} ratio={self.ratio} is_vg={self.is_vg}>"
  

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
  nic_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nic_profiles.id", ondelete="CASCADE"), index=True)
  nic_base_option_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nic_base_options.id"), index=True)
  ratio: Mapped[float] = mapped_column(Numeric(7, 6))

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
  

class NicProfile(Base):
  __tablename__ = "nic_profiles"

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  formula_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("formulas.id", ondelete="CASCADE"), index=True)

  slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
  name: Mapped[str] = mapped_column(String(255))
  
  is_pre_mix: Mapped[bool] = mapped_column(Boolean, default=False)

  is_old_mix: Mapped[bool] = mapped_column(Boolean, default=False)

  target_nic_str: Mapped[float] = mapped_column(Numeric(7, 6))
  target_vg: Mapped[float] = mapped_column(Numeric(7, 6))
  target_pg: Mapped[float] = mapped_column(Numeric(7, 6))
  nic_base_nic_str: Mapped[float] = mapped_column(Numeric(7, 6))

  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )

  formula: Mapped["Formula"] = relationship(back_populates="nic_profiles")

  nic_bases: Mapped[list["NicBase"]] = relationship(
    back_populates="nic_profile", cascade="all, delete-orphan"
  )
  flavorings: Mapped[list["Flavoring"]] = relationship(
    back_populates="nic_profile", cascade="all, delete-orphan"
  )
  
  @property
  def full_name(self) -> str:
    suffix = " - Old Mix" if self.is_old_mix else ""
    return f"{self.formula.name} - {self.name}{suffix}"

  def __repr__(self) -> str:
    return f"<NicProfile {self.slug!r}>"
  
 
class ProductionOrderCounter(Base):
  __tablename__ = "production_order_counters"

  date: Mapped[date] = mapped_column(Date, primary_key=True)
  last_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
  
class ProductionOrderStatus(enum.Enum):
  CANCELLED = "cancelled"
  DELIVERED = "delivered"
  FULFILLED = "fulfilled"
  IN_PROGRESS = "in_progress"
  PENDING = "pending"
  

production_order_status_enum = Enum(ProductionOrderStatus, name="productionorderstatus")


class ProductionOrderJob(enum.Enum):
  MIX = "mix"
  REPAT = "repat"


production_order_job_enum = Enum(ProductionOrderJob, name="productionorderjob")


class ProductionOrder(Base):
  __tablename__ = "production_orders"
  
  __table_args__ = (
    Index(
      "ix_production_orders_active",
      "created_at",
      postgresql_where=text("is_archived = false")
    ),
  )

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  order_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
  eliquid_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eliquids.id"), index=True)
  ordered_quantity: Mapped[int | None]
  fulfilled_quantity: Mapped[int | None]
  status: Mapped[ProductionOrderStatus] = mapped_column(production_order_status_enum, default=ProductionOrderStatus.PENDING)
  job: Mapped[ProductionOrderJob | None] = mapped_column(production_order_job_enum)
  is_priority: Mapped[bool] = mapped_column(Boolean, default=False)
  is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )
  
  allocations: Mapped[list["ProductionOrderAllocation"]] = relationship(
    back_populates="production_order", cascade="all, delete-orphan", passive_deletes=True
  )

  eliquid: Mapped["Eliquid"] = relationship(back_populates="production_orders")
  
  activity_logs: Mapped[list["ProductionOrderActivityLog"]] = relationship(
    back_populates="production_order", cascade="all, delete-orphan"
  )
  
  production_order_repat_jobs: Mapped[list["ProductionOrderRepatJob"]] = relationship(
    back_populates="production_order", cascade="all, delete-orphan"
  )
  
  production_order_mix_jobs: Mapped[list["ProductionOrderMixJob"]] = relationship(
    back_populates="production_order", cascade="all, delete-orphan"
  )
  
  @property
  def hq_quantity(self) -> int | None:
    if self.ordered_quantity is None:
      return None
    return self.ordered_quantity - sum(a.quantity for a in self.allocations)

  def __repr__(self) -> str:
    return f"<ProductionOrder {self.order_number!r} eliquid={self.eliquid.description!r} quantity={self.ordered_quantity} status={self.status.value}>"
  

class ProductionOrderActivity(enum.Enum):
  CREATED = "created"
  ADJUST_QUANTITY = "quantity"
  CHANGE_STATUS = "status"
  SWITCH_PRIORITY = "is_priority"
  TOGGLE_ARCHIVED = "is_archived"
  ASSIGN_JOB = "job"


production_order_activity_enum = Enum(ProductionOrderActivity, name="productionorderactivity")


class ProductionOrderActivityLog(Base):
  __tablename__ = "production_order_activity_logs"
  
  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  production_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"), index=True)
  activity: Mapped[ProductionOrderActivity] = mapped_column(production_order_activity_enum)
  old_value: Mapped[str | None] = mapped_column(String(255))
  new_value: Mapped[str | None] = mapped_column(String(255))
  triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  
  production_order: Mapped["ProductionOrder"] = relationship(back_populates="activity_logs")
  
  def __repr__(self) -> str:
    return f"<ProductionOrderActivityLog {self.production_order.order_number!r} activity={self.activity} old_value={self.old_value} new_value={self.new_value}>"
  

class ProductionOrderRepatJobStatus(enum.Enum):
  CANCELLED = "cancelled"
  COMPLETED = "completed"
  IN_PROGRESS = "in_progress"
  REASSIGNED = "reassigned"


production_order_repat_job_status_enum = Enum(ProductionOrderRepatJobStatus, name="productionorderjobstatus")


class ProductionOrderRepatJob(Base):
  __tablename__ = "production_order_repat_jobs"
  
  __table_args__ = (
    Index(
      "ix_production_order_repat_jobs_one_active_per_order",
      "production_order_id",
      unique=True,
      postgresql_where=text("status = 'IN_PROGRESS'")
    ),
  )
  
  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  production_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"), index=True)
  production_order_number: Mapped[str] = mapped_column(String(20), index=True)
  ordered_quantity: Mapped[int | None]
  incoming_quantity: Mapped[int | None]
  status: Mapped[ProductionOrderRepatJobStatus] = mapped_column(production_order_repat_job_status_enum, default=ProductionOrderRepatJobStatus.IN_PROGRESS)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )
  
  production_order: Mapped["ProductionOrder"] = relationship(back_populates="production_order_repat_jobs")
  
  def __repr__(self):
    return f"<ProductionOrderRepatriation {self.production_order_number!r} quantity={self.ordered_quantity} status={self.status.value}>"


class ProductionOrderMixJobStatus(enum.Enum):
  CANCELLED = "cancelled"
  COMPLETED = "completed"
  IN_PROGRESS = "in_progress"
  MIXED = "mixed"
  REASSIGNED = "reassigned"
  
  
production_order_mix_job_status_enum = Enum(ProductionOrderMixJobStatus, name="productionordermixjobstatus")


class ProductionOrderMixJob(Base):
  __tablename__ = "production_order_mix_jobs"
  
  __table_args__ = (
    Index(
      "ix_production_order_mix_jobs_one_active_per_order",
      "production_order_id",
      unique=True,
      postgresql_where=text("status = 'IN_PROGRESS'")
    ),
  )
  
  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  production_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"), index=True)
  production_order_number: Mapped[str] = mapped_column(String(20), index=True)
  ordered_quantity: Mapped[int]
  produced_quantity: Mapped[int | None]
  batch_number: Mapped[str | None] = mapped_column(String(255))
  recipe_snapshot: Mapped[dict | None] = mapped_column(JSONB)
  total_volume_ml: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
  total_weight_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
  status: Mapped[ProductionOrderMixJobStatus] = mapped_column(production_order_mix_job_status_enum, default=ProductionOrderMixJobStatus.IN_PROGRESS)
  is_priority: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )
  
  production_order: Mapped["ProductionOrder"] = relationship(back_populates="production_order_mix_jobs")
  
  def __repr__(self):
    return f"<ProductionOrderMix {self.production_order_number!r} quantity={self.ordered_quantity} status={self.status.value}>"

class ProductionOrderAllocation(Base):
  __tablename__ = "production_order_allocations"
  
  __table_args__ = (
    UniqueConstraint("production_order_id", "location_id", name="uq_allocation_order_location"),
    CheckConstraint("quantity > 0", name="ck_allocation_quantity_positive"),
  )
  
  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  production_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"), index=True)
  location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("locations.id"), index=True)
  quantity: Mapped[int]
  
  production_order: Mapped["ProductionOrder"] = relationship(back_populates="allocations")
  
  location: Mapped["Location"] = relationship()
  
  def __repr__(self):
    return f"<{self.__class__.__name__} {self.quantity}>"

class Location(Base):
  __tablename__ = "locations"
  
  __table_args__ = (
    Index("uq_locations_single_hq", "is_hq", unique=True, postgresql_where=text("is_hq")),
  )
  
  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  code: Mapped[str] = mapped_column(String(20), index=True, unique=True)
  name: Mapped[str] = mapped_column(String(255))
  address: Mapped[str] = mapped_column(String(255))
  city: Mapped[str] = mapped_column(String(255))
  province: Mapped[str] = mapped_column(String(255))
  is_hq: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )
  
  def __repr__(self) -> str:
    return f"<Location {self.name!r}>"