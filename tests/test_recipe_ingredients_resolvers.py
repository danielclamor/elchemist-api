from types import SimpleNamespace
 
import pytest
 
from api_graphql.resolvers.recipe_ingredients import (
  get_flavoring_ingredients,
  get_nic_base_ingredients,
  get_pg_ingredient,
  get_vg_ingredient,
  get_recipe_ingredients,
)

VG_FLAVOR_DENSITY = 1.16065
PG_FLAVOR_DENSITY = 1.04865
VG_DENSITY = 1.26130
PG_DENSITY = 1.03730
NIC_DENSITY = 1.00925

BATCH_VOLUME = 1000

def make_flavoring(ratio: float, is_vg: bool, name: str = "Flavour"):
  return SimpleNamespace(
    ratio=ratio,
    flavoring_option=SimpleNamespace(name=name, is_vg=is_vg),
  )

def make_nic_base(ratio: float, is_vg: bool, code: str = "1"):
  return SimpleNamespace(
    ratio=ratio,
    nic_base_option=SimpleNamespace(code=code, is_vg=is_vg)
  )

class TestGetFlavoringIngredient:
  def test_pg_flavorings(self):
    flavorings = [
      make_flavoring(ratio=0.25, is_vg=False, name="Flavour 1"),
      make_flavoring(ratio=0.25, is_vg=False, name="Flavour 2"),
    ]
    
    result = get_flavoring_ingredients(flavorings=flavorings, batch_volume_ml=BATCH_VOLUME)
    
    for i in result.ingredients:
      assert i.volume_ml == pytest.approx(250.0)
      assert i.weight_g == pytest.approx(250.0 * PG_FLAVOR_DENSITY)
    
    assert result.total_pg_ratio == 0.5
    assert result.total_vg_ratio == 0.0
  
  def test_vg_flavorings(self):
    flavorings = [
      make_flavoring(ratio=0.25, is_vg=True, name="Flavour 1"),
      make_flavoring(ratio=0.25, is_vg=True, name="Flavour 2"),
    ]
    
    result = get_flavoring_ingredients(flavorings=flavorings, batch_volume_ml=BATCH_VOLUME)
    
    for i in result.ingredients:
      assert i.volume_ml == pytest.approx(250.0)
      assert i.weight_g == pytest.approx(250.0 * VG_FLAVOR_DENSITY)
    
    assert result.total_pg_ratio == 0.0
    assert result.total_vg_ratio == 0.5
    
  def test_zero_ratio_gives_zero_volume_and_weight(self):
    flavorings = [
      make_flavoring(ratio=0.0, is_vg=True, name="Flavour 1"),
    ]
    
    result = get_flavoring_ingredients(flavorings=flavorings, batch_volume_ml=BATCH_VOLUME)
        
    for i in result.ingredients:
      assert i.volume_ml == pytest.approx(0.0)
      assert i.weight_g == pytest.approx(0.0)
    
    assert result.total_vg_ratio == 0.0
    assert result.total_pg_ratio == 0.0
    
class TestGetNicBaseIngredient:
  def test_pg_nic_bases(self):
    nic_bases = [
      make_nic_base(ratio=1.0, is_vg=False, code="2P")
    ]
    
    result = get_nic_base_ingredients(nic_bases=nic_bases, batch_volume_ml=BATCH_VOLUME, target_nic_str=0.02, nic_base_nic_str=0.1)
    
    for i in result.ingredients:
      assert i.name == "Nic Base (2P)"
      assert i.volume_ml == pytest.approx(200.0)
      assert i.weight_g == pytest.approx((20.0 * NIC_DENSITY) + (180.0 * PG_DENSITY))
    
    assert result.total_pg_ratio == 1.0
    assert result.total_vg_ratio == 0.0
    
  def test_vg_nic_bases(self):
    nic_bases = [
      make_nic_base(ratio=1.0, is_vg=True, code="1")
    ]
    
    result = get_nic_base_ingredients(nic_bases=nic_bases, batch_volume_ml=BATCH_VOLUME, target_nic_str=0.02, nic_base_nic_str=0.1)
    
    for i in result.ingredients:
      assert i.name == "Nic Base (1)"
      assert i.volume_ml == pytest.approx(200.0)
      assert i.weight_g == pytest.approx((20.0 * NIC_DENSITY) + (180.0 * VG_DENSITY))
    
    assert result.total_pg_ratio == 0.0
    assert result.total_vg_ratio == 1.0
    
  def test_zero_nic_str_gives_zero_volume_and_weight(self):
    nic_bases = [
      make_nic_base(ratio=1.0, is_vg=True, code="1")
    ]
    
    result = get_nic_base_ingredients(nic_bases=nic_bases, batch_volume_ml=BATCH_VOLUME, target_nic_str=0.02, nic_base_nic_str=0.0)
    
    for i in result.ingredients:
      assert i.name == "Nic Base (1)"
      assert i.volume_ml == pytest.approx(0.0)
      assert i.weight_g == pytest.approx(0.0)

class TestGetPgIngredient:
  def test_computes_expected_pg_volume_and_weight(self):
    total_pg_flavoring_batch_ratio = 0.5
    
    total_pg_nic_base_batch_ratio = 0.0
    
    nic_base_nic_str = 0.1
    
    target_nic_str = 0.02
    target_pg = 0.6
    
    expected_pg_ratio = target_pg - total_pg_flavoring_batch_ratio + (target_nic_str * (total_pg_nic_base_batch_ratio - target_pg - (total_pg_nic_base_batch_ratio / nic_base_nic_str)))
    expected_pg_volume = expected_pg_ratio * BATCH_VOLUME
    expected_pg_weight = expected_pg_volume * PG_DENSITY
    
    result = get_pg_ingredient(
      total_pg_flavoring_batch_ratio=total_pg_flavoring_batch_ratio,
      total_pg_nic_base_batch_ratio=total_pg_nic_base_batch_ratio,
      target_nic_str=target_nic_str,
      target_pg=target_pg,
      nic_base_nic_str=nic_base_nic_str,
      batch_volume_ml=BATCH_VOLUME
    )
    
    assert result.ratio == expected_pg_ratio
    assert result.volume_ml == expected_pg_volume
    assert result.weight_g == expected_pg_weight
    
  def test_name_is_pg_not_vg(self):
    result = get_pg_ingredient(
      total_pg_flavoring_batch_ratio=0.5,
      total_pg_nic_base_batch_ratio=0.0,
      target_nic_str=0.02,
      target_pg=0.6,
      nic_base_nic_str=0.1,
      batch_volume_ml=BATCH_VOLUME
    )
    
    assert result.name == "PG"
    
class TestGetVgIngredient:
  def test_computes_expected_vg_volume_and_weight(self):
    total_vg_flavoring_batch_ratio = 0.0
    
    total_vg_nic_base_batch_ratio = 1.0
    
    nic_base_nic_str = 0.1
    
    target_nic_str = 0.02
    target_vg = 0.4
    
    expected_vg_ratio = target_vg - total_vg_flavoring_batch_ratio + (target_nic_str * (total_vg_nic_base_batch_ratio - target_vg - (total_vg_nic_base_batch_ratio / nic_base_nic_str)))
    expected_vg_volume = expected_vg_ratio * BATCH_VOLUME
    expected_vg_weight = expected_vg_volume * VG_DENSITY
    
    result = get_vg_ingredient(
      total_vg_flavoring_batch_ratio=total_vg_flavoring_batch_ratio,
      total_vg_nic_base_batch_ratio=total_vg_nic_base_batch_ratio,
      target_nic_str=target_nic_str,
      target_vg=target_vg,
      nic_base_nic_str=nic_base_nic_str,
      batch_volume_ml=BATCH_VOLUME
    )
    
    assert result.ratio == expected_vg_ratio
    assert result.volume_ml == expected_vg_volume
    assert result.weight_g == expected_vg_weight
    
  def test_name_is_vg_not_pg(self):
    result = get_vg_ingredient(
      total_vg_flavoring_batch_ratio=0.5,
      total_vg_nic_base_batch_ratio=1.0,
      target_nic_str=0.02,
      target_vg=0.6,
      nic_base_nic_str=0.1,
      batch_volume_ml=BATCH_VOLUME
    )
    
    assert result.name == "VG"

class TestGetRecipeIngredients:
  def test_returns_all_ingredients_with_real_math(self, mocker):
    target_nic_str = 0.02
    target_vg = 0.4
    target_pg = 0.6
    nic_base_nic_str = 0.1
    
    flavorings = [
      make_flavoring(ratio=0.25, is_vg=False, name="Flavour 1"),
      make_flavoring(ratio=0.25, is_vg=False, name="Flavour 2"),
    ]
    total_pg_flavoring_batch_ratio = sum(f.ratio for f in flavorings if f.flavoring_option.is_vg is False)
    total_vg_flavoring_batch_ratio = sum(f.ratio for f in flavorings if f.flavoring_option.is_vg is True)
    
    nic_bases = [
      make_nic_base(ratio=1.0, is_vg=True, code="1")
    ]
    total_pg_nic_base_batch_ratio = sum(b.ratio for b in nic_bases if b.nic_base_option.is_vg is False)
    total_vg_nic_base_batch_ratio = sum(b.ratio for b in nic_bases if b.nic_base_option.is_vg is True)
    
    nic_profile = SimpleNamespace(
      target_nic_str=target_nic_str,
      target_vg=target_vg,
      target_pg=target_pg,
      nic_base_nic_str=nic_base_nic_str,
      flavorings=flavorings,
      nic_bases=nic_bases
    )
    
    mocker.patch(
      "api_graphql.resolvers.recipe_ingredients.get_nic_profile",
      return_value=nic_profile,
    )
    
    result = get_recipe_ingredients(
      db=mocker.MagicMock(),
      nic_profile_identifier=mocker.MagicMock(),
      batch_volume_ml=BATCH_VOLUME
    )
    
    assert len(result) == 5
    
    names = [r.name for r in result]
    assert "Nic Base (1)" in names
    assert "Flavour 1" in names
    assert "Flavour 2" in names
    assert "PG" in names
    assert "VG" in names
    
    expected_pg_ratio = target_pg - total_pg_flavoring_batch_ratio + (target_nic_str * (total_pg_nic_base_batch_ratio - target_pg - (total_pg_nic_base_batch_ratio / nic_base_nic_str)))
    expected_pg_volume = expected_pg_ratio * BATCH_VOLUME
    expected_pg_weight = expected_pg_volume * PG_DENSITY
    
    expected_vg_ratio = target_vg - total_vg_flavoring_batch_ratio + (target_nic_str * (total_vg_nic_base_batch_ratio - target_vg - (total_vg_nic_base_batch_ratio / nic_base_nic_str)))
    expected_vg_volume = expected_vg_ratio * BATCH_VOLUME
    expected_vg_weight = expected_vg_volume * VG_DENSITY
    
    pg_result = next(r for r in result if r.name == "PG")
    vg_result = next(r for r in result if r.name == "VG")
    
    assert pg_result.weight_g == expected_pg_weight
    assert vg_result.weight_g == expected_vg_weight
    
  def test_raises_when_nic_profile_not_found(self, mocker):
    mocker.patch(
      "api_graphql.resolvers.nic_profile.get_nic_profile",
      return_value=None,
    )
    
    with pytest.raises(Exception):
      get_recipe_ingredients(
        db=mocker.MagicMock(),
        nic_profile_identifier=mocker.MagicMock(),
        batch_volume_ml=BATCH_VOLUME
      )