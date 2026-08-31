import enum
import uuid
from datetime import datetime, timezone, date

from sqlalchemy import (
  Boolean,
  Date,
  DateTime,
  Enum,
  ForeignKey,
  Integer,
  Numeric,
  String,
  func,
)
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


class NicType(enum.Enum):
  FREEBASE = "freebase"
  SALT = "salt"


chill_type_enum = Enum(ChillType, name="chilltype")
nic_type_enum = Enum(NicType, name="nictype")


class SizeOption(enum.Enum):
  ML_30 = "30ml"
  ML_60 = "60ml"
  ML_120 = "120ml"


class NicLevelOption(enum.Enum):
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


size_option_enum = Enum(SizeOption, name="sizeoption")
nic_level_option_enum = Enum(NicLevelOption, name="nicleveloption")


class Eliquid(Base):
  __tablename__ = "eliquids"

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  upc: Mapped[str] = mapped_column(String(12), unique=True, index=True)
  description: Mapped[str] = mapped_column(String(255))
  brand: Mapped[str] = mapped_column(String(255))
  chill_type: Mapped[ChillType] = mapped_column(chill_type_enum)
  nic_type: Mapped[NicType] = mapped_column(nic_type_enum)
  size: Mapped[SizeOption] = mapped_column(size_option_enum)
  nic_level: Mapped[NicLevelOption] = mapped_column(nic_level_option_enum)
  bottle_color: Mapped[BottleColor] = mapped_column(bottle_color_enum)
  nic_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nic_profiles.id", ondelete="SET NULL"), nullable=True)

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
  nic_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nic_profiles.id", ondelete="CASCADE"))
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
  nic_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nic_profiles.id", ondelete="CASCADE"))
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
  

class NicProfile(Base):
  __tablename__ = "nic_profiles"

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  formula_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("formulas.id", ondelete="CASCADE"))

  slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
  name: Mapped[str] = mapped_column(String(255))
  
  is_pre_mix: Mapped[bool] = mapped_column(Boolean, default=False)

  is_old_mix: Mapped[bool] = mapped_column(Boolean, default=False)

  target_nic_str: Mapped[float] = mapped_column(Numeric(6, 3))
  target_vg: Mapped[float] = mapped_column(Numeric(6, 3))
  target_pg: Mapped[float] = mapped_column(Numeric(6, 3))
  nic_base_nic_str: Mapped[float] = mapped_column(Numeric(6, 3))

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
  MIXED = "mixed"
  PENDING = "pending"
  

production_order_status_enum = Enum(ProductionOrderStatus, name="productionorderstatus")


class ProductionOrder(Base):
  __tablename__ = "production_orders"

  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  order_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
  eliquid_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eliquids.id"))
  quantity: Mapped[int] = mapped_column()
  status: Mapped[ProductionOrderStatus] = mapped_column(production_order_status_enum, default=ProductionOrderStatus.PENDING)
  is_priority: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )

  eliquid: Mapped["Eliquid"] = relationship(back_populates="production_orders")
  
  activity_logs: Mapped[list["ProductionOrderActivityLog"]] = relationship(
    back_populates="production_order", cascade="all, delete-orphan"
  )

  def __repr__(self) -> str:
    return f"<ProductionOrder {self.order_number!r} eliquid={self.eliquid.description!r} quantity={self.quantity} status={self.status.value}>"
  

class ProductionOrderActivity(enum.Enum):
  CREATED = "created"
  ADJUST_QUANTITY = "adjust_quantity"
  CHANGE_STATUS = "change_status"
  SWITCH_PRIORITY = "switch_priority"


production_order_activity_enum = Enum(ProductionOrderActivity, name="productionorderactivity")


class ProductionOrderActivityLog(Base):
  __tablename__ = "production_order_activity_logs"
  
  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  production_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"))
  activity: Mapped[ProductionOrderActivity] = mapped_column(production_order_activity_enum)
  old_value: Mapped[str] = mapped_column(String(255), nullable=True)
  new_value: Mapped[str] = mapped_column(String(255), nullable=True)
  triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  
  production_order: Mapped["ProductionOrder"] = relationship(back_populates="activity_logs")
  
  def __repr__(self) -> str:
    return f"<ProductionOrderActivityLog {self.order_number!r} production_order={self.production_order.order_number!r} activity={self.activity} old_value={self.old_value} new_value={self.new_value}>"