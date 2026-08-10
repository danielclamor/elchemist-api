import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from models import ChillType, NicType


# --- NicBaseOption ---


class NicBaseOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    is_vg: bool


# --- NicBase ---


class NicBaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ratio: float
    nic_base_option: NicBaseOptionOut


class NicBaseCreate(BaseModel):
    nic_base_option_id: uuid.UUID
    ratio: float


# --- Flavoring ---


class FlavoringOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    ratio: float
    is_vg: bool


class FlavoringCreate(BaseModel):
    name: str
    ratio: float
    is_vg: bool


# --- NicProfile ---


class NicProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    full_name: str | None
    is_new_mix: bool
    target_nic_strength: float
    target_vg: float
    target_pg: float
    nic_base_nic_strength: float
    nic_bases: list[NicBaseOut] = []
    flavorings: list[FlavoringOut] = []


class NicProfileCreate(BaseModel):
    slug: str
    name: str
    full_name: str | None = None
    is_new_mix: bool = False
    target_nic_strength: float
    target_vg: float
    target_pg: float
    nic_base_nic_strength: float
    nic_bases: list[NicBaseCreate] = []
    flavorings: list[FlavoringCreate] = []


# --- Formula ---


class FormulaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    brand: str
    chill_type: ChillType
    nic_type: NicType
    created_at: datetime
    updated_at: datetime
    nic_profiles: list[NicProfileOut] = []


class FormulaCreate(BaseModel):
    slug: str
    name: str
    brand: str
    chill_type: ChillType
    nic_type: NicType
