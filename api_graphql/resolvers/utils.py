from typing import TYPE_CHECKING
from datetime import datetime
from zoneinfo import ZoneInfo
import dataclasses
import json
import strawberry

if TYPE_CHECKING:
  from datetime import date

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

def generate_production_order_number(date: date, counter: int) -> str:
  return f"{date:%Y%m%d}{counter:05d}"

def convert_strawberry_input_to_dict(input_obj):
    data = dataclasses.asdict(input_obj)
    return {k: v for k, v in data.items() if v is not strawberry.UNSET}