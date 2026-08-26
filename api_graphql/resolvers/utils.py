from typing import TYPE_CHECKING
from datetime import datetime
from zoneinfo import ZoneInfo

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
  return f"PROD-{date:%Y%m%d}-{counter:06d}"