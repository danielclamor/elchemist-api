from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo
import dataclasses
import json
import strawberry

def generate_slug(string: str) -> str:
  import re
  tokens = re.sub(r'[^a-zA-Z0-9]', ' ', string).strip().split(' ')
  tokens = [token for token in tokens if token != ""]
  return '-'.join(tokens).lower()

def get_today(timezone: str | None = None) -> datetime:
  if timezone:
    return datetime.now(ZoneInfo(timezone))

  import os 
  from dotenv import load_dotenv
  load_dotenv()
  
  return datetime.now(ZoneInfo(os.getenv("TIMEZONE")))

def generate_production_order_number(counter: int) -> str:
  return str(counter)

def generate_session_number(day: date, counter: int) -> str:
  return f"MIX-{day:%Y%m%d}-{counter}"

def generate_batch_code(datetime: datetime, suffix: str = "") -> str:
  return f'{datetime:%m%d%y%H%M}{suffix}'

def convert_strawberry_input_to_dict(obj):
  # data = dataclasses.asdict(obj)
  # return {k: v for k, v in data.items() if v is not strawberry.UNSET}
  if dataclasses.is_dataclass(obj):
    return {
      f.name: convert_strawberry_input_to_dict(getattr(obj, f.name))
      for f in dataclasses.fields(obj)
      if getattr(obj, f.name) is not strawberry.UNSET
      and not callable(getattr(obj, f.name))
    }
  if isinstance(obj, list):
    return [convert_strawberry_input_to_dict(item) for item in obj]
  if isinstance(obj, dict):
    return {
      k: convert_strawberry_input_to_dict(v)
      for k, v in obj.items()
      if v is not strawberry.UNSET and not callable(v)
    }
  return obj