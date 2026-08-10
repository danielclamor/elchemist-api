import json
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import (
    ChillType,
    Flavoring,
    Formula,
    NicBase,
    NicBaseOption,
    NicProfile,
    NicType,
)

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))


def get_or_create_nic_base_option(session: Session, code: str, name: str, is_vg: bool) -> NicBaseOption:
    option = session.scalar(select(NicBaseOption).where(NicBaseOption.code == code))
    if option:
      return option

    print(f"  NicBaseOption {code!r} not found — creating it")
    option = NicBaseOption(code=code, name=name, is_vg=is_vg)
    session.add(option)
    session.flush()  # so option.id is available immediately
    return option


def import_formula(session: Session, data: dict) -> Formula:
  existing = session.scalar(select(Formula).where(Formula.slug == data["slug"]))
  if existing:
    print(f"Skipping — formula {data['slug']!r} already exists")
    return existing

  formula = Formula(
    slug=data["slug"],
    name=data["name"],
    brand=data["brand"],
    chill_type=ChillType(data["chill_type"]),
    nic_type=NicType(data["nic_type"]),
  )

  for profile_data in data["nic_profiles"]:
    nic_profile = NicProfile(
      slug=profile_data["slug"],
      name=profile_data["name"],
      full_name=profile_data.get("full_name"),
      is_new_mix=profile_data["is_new_mix"],
      target_nic_str=profile_data["target_nic_str"],
      target_vg=profile_data["target_vg"],
      target_pg=profile_data["target_pg"],
      nic_base_nic_str=profile_data["nic_base_nic_str"],
    )

    for nb_data in profile_data.get("nic_bases", []):
      option_data = nb_data["nic_base"]
      option = get_or_create_nic_base_option(
        session,
        code=option_data["code"],
        name=option_data["name"],
        is_vg=option_data["is_vg"],
      )
      nic_profile.nic_bases.append(
        NicBase(nic_base_option=option, ratio=nb_data["ratio"])
      )

    for fl_data in profile_data.get("flavorings", []):
      nic_profile.flavorings.append(
        Flavoring(
          name=fl_data["name"],
          ratio=fl_data["ratio"],
          is_vg=fl_data["is_vg"],
        )
      )

    formula.nic_profiles.append(nic_profile)

  session.add(formula)
  return formula


if __name__ == "__main__":
  path = sys.argv[1] if len(sys.argv) > 1 else "formulas.json"

  with open(path) as f:
    data = json.load(f)

  with Session(engine) as session:
    for formula_data in data:
      formula = import_formula(session, formula_data)
      session.commit()
      session.refresh(formula)

      print(f"\nImported: {formula.name} ({formula.brand})")
      for np in formula.nic_profiles:
        print(f"  {np.name}: {len(np.nic_bases)} nic base(s), {len(np.flavorings)} flavoring(s)")