import os
 
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
 
from models import NicBaseOption
 
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

SEED_OPTIONS=[
  {"code": "1", "name": "VG S", "is_vg": True},
  {"code": "2P", "name": "PG F", "is_vg": False},
  {"code": "3P", "name": "VG F", "is_vg": True},
  {"code": "1CNT", "name": "VG S", "is_vg": True},
  {"code": "2CNT", "name": "PG S", "is_vg": False},
]

with Session(engine) as session:
  for option in SEED_OPTIONS:
    print(option)
    existing = session.scalar(select(NicBaseOption).where(NicBaseOption.code == option["code"]))
    
    if existing:
      print(f"Skipping {option['code']} — already exists")
      continue
      
    session.add(NicBaseOption(**option))
    print(f"Added {option['code']}")
  
  session.commit()