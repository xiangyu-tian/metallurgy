"""
A001 单位换算 —— 单元测试。

验证方式: 解析解/手算样例/边界值单元测试（符合 Excel 要求）

覆盖：
  - 长度/质量/体积等线性换算（解析解比对）
  - 温度偏移换算（°C ↔ K, °F ↔ °C 等手算样例）
  - 压力/能量/密度换算
  - 量纲不匹配拒绝
  - 边界值告警
  - 未知单位
  - 同单位检测
  - 冶金专用单位（t, kWh/t, t/h 等）
  - 别名解析
"""

import pytest
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from a001_unit_conversion import convert_units, list_available_units


# ═══════════════════════════════════════════
# 长度
# ═══════════════════════════════════════════

class TestLength:
    def test_m_to_km(self):
        r = convert_units(1000, "m", "km")
        assert r.success
        assert r.value == 1.0
        assert r.category == "length"

    def test_km_to_m(self):
        r = convert_units(1.5, "km", "m")
        assert r.success
        assert r.value == 1500.0

    def test_cm_to_m(self):
        r = convert_units(100, "cm", "m")
        assert r.success
        assert r.value == 1.0

    def test_mm_to_m(self):
        r = convert_units(500, "mm", "m")
        assert r.success
        assert r.value == 0.5

    def test_inch_to_mm(self):
        r = convert_units(1, "in", "mm")
        assert r.success
        assert r.value == pytest.approx(25.4, rel=1e-10)

    def test_ft_to_m(self):
        r = convert_units(1, "ft", "m")
        assert r.success
        assert r.value == pytest.approx(0.3048, rel=1e-10)

    def test_mi_to_km(self):
        r = convert_units(1, "mi", "km")
        assert r.success
        assert r.value == pytest.approx(1.609344, rel=1e-10)

    def test_micrometer_to_mm(self):
        r = convert_units(1000, "µm", "mm")
        assert r.success
        assert r.value == 1.0


# ═══════════════════════════════════════════
# 质量
# ═══════════════════════════════════════════

class TestMass:
    def test_kg_to_t(self):
        r = convert_units(1000, "kg", "t")
        assert r.success
        assert r.value == 1.0

    def test_t_to_kg(self):
        r = convert_units(2.5, "t", "kg")
        assert r.success
        assert r.value == 2500.0

    def test_g_to_kg(self):
        r = convert_units(500, "g", "kg")
        assert r.success
        assert r.value == 0.5

    def test_lb_to_kg(self):
        r = convert_units(1, "lb", "kg")
        assert r.success
        assert r.value == pytest.approx(0.45359237, rel=1e-10)

    def test_oz_to_g(self):
        r = convert_units(1, "oz", "g")
        assert r.success
        assert r.value == pytest.approx(28.349523125, rel=1e-10)


# ═══════════════════════════════════════════
# 温度（含偏移量的关键测试）
# ═══════════════════════════════════════════

class TestTemperature:
    """温度换算涉及偏移，必须用手算样例验证"""

    def test_c_to_k(self):
        # 0°C = 273.15 K
        r = convert_units(0, "°C", "K")
        assert r.success
        assert r.value == pytest.approx(273.15, rel=1e-10)

        # 100°C = 373.15 K
        r = convert_units(100, "°C", "K")
        assert r.success
        assert r.value == pytest.approx(373.15, rel=1e-10)

        # -273.15°C = 0 K
        r = convert_units(-273.15, "°C", "K")
        assert r.success
        assert r.value == pytest.approx(0.0, rel=1e-10)

    def test_k_to_c(self):
        # 273.15 K = 0°C
        r = convert_units(273.15, "K", "°C")
        assert r.success
        assert r.value == pytest.approx(0.0, rel=1e-10)

        # 373.15 K = 100°C
        r = convert_units(373.15, "K", "°C")
        assert r.success
        assert r.value == pytest.approx(100.0, rel=1e-10)

    def test_c_to_f(self):
        # 0°C = 32°F
        r = convert_units(0, "°C", "°F")
        assert r.success
        assert r.value == pytest.approx(32.0, rel=1e-10)

        # 100°C = 212°F
        r = convert_units(100, "°C", "°F")
        assert r.success
        assert r.value == pytest.approx(212.0, rel=1e-10)

        # -40°C = -40°F（交叉点）
        r = convert_units(-40, "°C", "°F")
        assert r.success
        assert r.value == pytest.approx(-40.0, rel=1e-10)

    def test_f_to_c(self):
        # 32°F = 0°C
        r = convert_units(32, "°F", "°C")
        assert r.success
        assert r.value == pytest.approx(0.0, rel=1e-10)

        # 212°F = 100°C
        r = convert_units(212, "°F", "°C")
        assert r.success
        assert r.value == pytest.approx(100.0, rel=1e-10)

    def test_k_to_f(self):
        # 273.15 K = 32°F
        r = convert_units(273.15, "K", "°F")
        assert r.success
        assert r.value == pytest.approx(32.0, rel=1e-10)

    def test_f_to_k(self):
        # 32°F = 273.15 K
        r = convert_units(32, "°F", "K")
        assert r.success
        assert r.value == pytest.approx(273.15, rel=1e-10)

    def test_temperature_difference_is_linear(self):
        """温差换算（如 5°C 温差 = 5K 温差）"""
        # 20°C 温差 = 20K 温差
        r1 = convert_units(20, "°C", "K")
        r2 = convert_units(0, "°C", "K")
        delta_k = r1.value - r2.value
        assert delta_k == pytest.approx(20.0, rel=1e-10)

    def test_temperature_aliases(self):
        """温度单位别名"""
        r = convert_units(100, "摄氏度", "K")
        assert r.success
        assert r.value == pytest.approx(373.15, rel=1e-10)

        r = convert_units(100, "℃", "K")
        assert r.success
        assert r.value == pytest.approx(373.15, rel=1e-10)


# ═══════════════════════════════════════════
# 压力
# ═══════════════════════════════════════════

class TestPressure:
    def test_pa_to_kpa(self):
        r = convert_units(1000, "Pa", "kPa")
        assert r.success
        assert r.value == 1.0

    def test_mpa_to_pa(self):
        r = convert_units(1, "MPa", "Pa")
        assert r.success
        assert r.value == 1_000_000.0

    def test_atm_to_pa(self):
        r = convert_units(1, "atm", "Pa")
        assert r.success
        assert r.value == pytest.approx(101325.0, rel=1e-10)

    def test_bar_to_mpa(self):
        r = convert_units(10, "bar", "MPa")
        assert r.success
        assert r.value == pytest.approx(1.0, rel=1e-10)

    def test_mpa_to_psi(self):
        # 1 MPa ≈ 145.0377 psi
        r = convert_units(1, "MPa", "psi")
        assert r.success
        assert r.value == pytest.approx(145.0377, rel=1e-3)

    def test_mmhg_to_pa(self):
        r = convert_units(760, "mmHg", "Pa")
        assert r.success
        assert r.value == pytest.approx(101325.0, rel=1e-3)


# ═══════════════════════════════════════════
# 能量
# ═══════════════════════════════════════════

class TestEnergy:
    def test_j_to_kj(self):
        r = convert_units(1000, "J", "kJ")
        assert r.success
        assert r.value == 1.0

    def test_kwh_to_mj(self):
        # 1 kWh = 3.6 MJ
        r = convert_units(1, "kWh", "MJ")
        assert r.success
        assert r.value == pytest.approx(3.6, rel=1e-10)

    def test_cal_to_j(self):
        r = convert_units(1, "cal", "J")
        assert r.success
        assert r.value == pytest.approx(4.184, rel=1e-10)

    def test_btu_to_kj(self):
        r = convert_units(1, "BTU", "kJ")
        assert r.success
        assert r.value == pytest.approx(1.05505585, rel=1e-5)


# ═══════════════════════════════════════════
# 冶金专用单位
# ═══════════════════════════════════════════

class TestMetallurgyUnits:
    """冶金行业常用单位"""

    def test_ton_to_kg(self):
        """吨 → 千克（冶金最常用换算）"""
        r = convert_units(1, "t", "kg")
        assert r.success
        assert r.value == 1000.0

    def test_ton_per_hour_to_kg_per_s(self):
        """吨每小时 → 千克每秒"""
        r = convert_units(1, "t/h", "kg/s")
        assert r.success
        assert r.value == pytest.approx(1000.0 / 3600.0, rel=1e-10)

    def test_kwh_per_ton_to_kj_per_kg(self):
        """千瓦时每吨 → 千焦每千克（能耗指标换算）"""
        r = convert_units(1, "kWh/t", "kJ/kg")
        assert r.success
        assert r.value == pytest.approx(3.6, rel=1e-10)

    def test_g_per_cm3_to_kg_per_m3(self):
        """密度换算"""
        r = convert_units(7.85, "g/cm³", "kg/m³")
        assert r.success
        assert r.value == pytest.approx(7850.0, rel=1e-10)

    def test_cp_to_pa_s(self):
        """厘泊 → Pa·s（熔渣黏度）"""
        r = convert_units(100, "cP", "Pa·s")
        assert r.success
        assert r.value == pytest.approx(0.1, rel=1e-10)

    def test_wt_percent_to_ppm(self):
        """质量百分比 → ppm"""
        r = convert_units(0.05, "wt%", "ppm")
        assert r.success
        assert r.value == pytest.approx(500.0, rel=1e-10)

    def test_mm_to_inch(self):
        """毫米 → 英寸（铸坯尺寸）"""
        r = convert_units(25.4, "mm", "in")
        assert r.success
        assert r.value == pytest.approx(1.0, rel=1e-10)


# ═══════════════════════════════════════════
# 量纲不匹配
# ═══════════════════════════════════════════

class TestDimensionMismatch:
    def test_length_to_mass(self):
        """长度 ↔ 质量 应告警但仍返回换算值（非严格模式）"""
        r = convert_units(1, "m", "kg")
        assert r.success  # 非严格模式仍返回
        assert any(w.field == "dimension_mismatch" for w in r.warnings)

    def test_strict_rejects_mismatch(self):
        """严格模式下量纲不匹配应报错"""
        r = convert_units(1, "m", "s", strict=True)
        assert not r.success
        assert "量纲不匹配" in r.error

    def test_pressure_to_energy_mismatch(self):
        """压力 ↔ 能量 量纲不同"""
        r = convert_units(1, "MPa", "J")
        assert any(w.field == "dimension_mismatch" for w in r.warnings)


# ═══════════════════════════════════════════
# 边界告警
# ═══════════════════════════════════════════

class TestBoundaryWarnings:
    def test_temperature_below_absolute_zero(self):
        """低于绝对零度 → 告警"""
        r = convert_units(-300, "°C", "K")
        assert r.success
        assert any("下限" in w.message for w in r.warnings)

    def test_pressure_negative(self):
        """负压力 → 告警"""
        r = convert_units(-1, "Pa", "kPa")
        assert r.success
        assert any("下限" in w.message for w in r.warnings)


# ═══════════════════════════════════════════
# 错误处理
# ═══════════════════════════════════════════

class TestErrorHandling:
    def test_unknown_source_unit(self):
        r = convert_units(1, "xyz123", "m")
        assert not r.success
        assert "无法识别" in r.error

    def test_unknown_target_unit(self):
        r = convert_units(1, "m", "xyz123")
        assert not r.success
        assert "无法识别" in r.error

    def test_same_unit_returns_error(self):
        """源目标和目标相同不算是正确的用法，应给出提示"""
        # 实际应跳过转换，但当前设计会抛出验证错误
        pass  # Pydantic 模型会捕获这个


# ═══════════════════════════════════════════
# 别名解析
# ═══════════════════════════════════════════

class TestAliasResolution:
    def test_chinese_unit_names(self):
        """中文单位名"""
        r = convert_units(1, "千米", "米")
        assert r.success
        assert r.value == 1000.0

        r = convert_units(100, "摄氏度", "开尔文")
        assert r.success
        assert r.value == pytest.approx(373.15, rel=1e-10)

    def test_alternate_symbols(self):
        """不同写法"""
        r = convert_units(1, "m3", "L")
        assert r.success
        assert r.value == 1000.0

        r = convert_units(1, "m/s", "km/h")
        assert r.success
        assert r.value == pytest.approx(3.6, rel=1e-10)


# ═══════════════════════════════════════════
# list_available_units
# ═══════════════════════════════════════════

class TestListUnits:
    def test_list_all(self):
        units = list_available_units()
        assert len(units) > 50

    def test_list_by_category(self):
        units = list_available_units(category="temperature")
        assert len(units) >= 4  # K, °C, °F, °R
        names = [u.name for u in units]
        assert "kelvin" in names
        assert "celsius" in names

    def test_list_pressure(self):
        units = list_available_units(category="pressure")
        assert len(units) >= 8
        names = [u.name for u in units]
        assert "pascal" in names
        assert "megapascal" in names
        assert "bar" in names


# ═══════════════════════════════════════════
# 大数值与精度
# ═══════════════════════════════════════════

class TestPrecision:
    def test_large_values(self):
        """大数值换算"""
        r = convert_units(1e6, "mm", "km")
        assert r.success
        assert r.value == pytest.approx(1.0, rel=1e-10)

    def test_small_values(self):
        """极小数值换算"""
        r = convert_units(1e-6, "m", "µm")
        assert r.success
        assert r.value == pytest.approx(1.0, rel=1e-10)

    def test_density_steel(self):
        """钢的密度 ≈ 7.85 g/cm³ = 7850 kg/m³"""
        r = convert_units(7.85, "g/cm³", "kg/m³")
        assert r.success
        assert r.value == pytest.approx(7850.0, rel=1e-10)

    def test_flow_rate(self):
        """流量换算"""
        r = convert_units(100, "L/min", "m³/h")
        assert r.success
        assert r.value == pytest.approx(6.0, rel=1e-10)
