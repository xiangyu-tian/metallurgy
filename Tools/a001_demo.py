"""
A001 单位换算 —— 演示脚本
展示冶金场景中的常用换算。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from a001_unit_conversion import convert_units, list_available_units


def print_result(r, label=""):
    """格式化打印换算结果"""
    status = "✓" if r.success else "✗"
    extra = ""
    if r.warnings:
        warnings_str = "; ".join(w.message for w in r.warnings)
        extra = f"  ⚠ {warnings_str}"
    if r.error:
        extra = f"  ❌ {r.error}"

    print(f"  {status} {label}: {r.source_value} {r.source_unit} → {r.value:.6g} {r.target_unit}"
          f"  [因子={r.conversion_factor:.6g}]"
          f"{extra}")


def demo():
    print("=" * 70)
    print("A001 单位换算 — 冶金场景演示")
    print("=" * 70)

    # ── 1. 长度 ──
    print("\n📏 长度换算")
    print_result(convert_units(100, "mm", "m"), "100 mm → m")
    print_result(convert_units(1, "in", "mm"), "1 in → mm")
    print_result(convert_units(200, "mm", "in"), "200 mm → in")
    print_result(convert_units(1.5, "km", "m"), "1.5 km → m")

    # ── 2. 质量 ──
    print("\n⚖️  质量换算")
    print_result(convert_units(250, "t", "kg"), "250 t → kg（转炉炉容）")
    print_result(convert_units(1, "t", "lb"), "1 t → lb")
    print_result(convert_units(50, "kg", "t"), "50 kg → t")

    # ── 3. 温度（最易出错）──
    print("\n🌡️  温度换算（注意偏移！）")
    print_result(convert_units(0, "°C", "K"), "0°C → K（冰点）")
    print_result(convert_units(25, "°C", "K"), "25°C → K（室温）")
    print_result(convert_units(1600, "°C", "K"), "1600°C → K（钢水温度）")
    print_result(convert_units(100, "°C", "°F"), "100°C → °F（沸点）")
    print_result(convert_units(-40, "°C", "°F"), "-40°C → °F（交叉点）")
    print_result(convert_units(273.15, "K", "°C"), "273.15 K → °C")

    # ── 4. 压力 ──
    print("\n💨 压力换算")
    print_result(convert_units(1, "atm", "Pa"), "1 atm → Pa")
    print_result(convert_units(2.5, "MPa", "bar"), "2.5 MPa → bar")
    print_result(convert_units(1, "MPa", "psi"), "1 MPa → psi")
    print_result(convert_units(760, "mmHg", "atm"), "760 mmHg → atm")

    # ── 5. 能量/能耗 ──
    print("\n⚡ 能量与能耗换算")
    print_result(convert_units(1, "kWh", "MJ"), "1 kWh → MJ")
    print_result(convert_units(100, "kWh/t", "kJ/kg"), "100 kWh/t → kJ/kg（吨钢能耗）")
    print_result(convert_units(1000, "kJ/kg", "kWh/t"), "1000 kJ/kg → kWh/t")
    print_result(convert_units(1, "GJ", "kWh"), "1 GJ → kWh")

    # ── 6. 冶金流量 ──
    print("\n🔧 流量换算")
    print_result(convert_units(100, "L/min", "m³/h"), "100 L/min → m³/h（冷却水）")
    print_result(convert_units(1, "t/h", "kg/s"), "1 t/h → kg/s（投料速率）")

    # ── 7. 密度 ──
    print("\n📦 密度换算")
    print_result(convert_units(7.85, "g/cm³", "kg/m³"), "钢密度 7.85 g/cm³ → kg/m³")
    print_result(convert_units(7850, "kg/m³", "g/cm³"), "7850 kg/m³ → g/cm³（反向检验）")

    # ── 8. 黏度 ──
    print("\n🫘 黏度换算")
    print_result(convert_units(500, "cP", "Pa·s"), "500 cP → Pa·s（熔渣黏度）")

    # ── 9. 浓度 ──
    print("\n📊 浓度换算")
    print_result(convert_units(0.05, "wt%", "ppm"), "0.05 wt% → ppm")
    print_result(convert_units(100, "ppm", "%"), "100 ppm → %")

    # ── 10. 边界告警 ──
    print("\n⚠️  边界告警示例")
    r = convert_units(-300, "°C", "K")
    print(f"  [-300°C → K] 结果={r.value:.2f} K")
    for w in r.warnings:
        print(f"    ⚠ {w.message}")

    # ── 11. 量纲不匹配告警 ──
    print("\n🚫 量纲不匹配示例")
    r = convert_units(100, "MPa", "kg")
    print(f"  [100 MPa → kg] 结果={r.value:.4f} kg（无物理意义）")
    for w in r.warnings:
        print(f"    🚩 {w.message}")

    # ── 12. 列出可用单位 ──
    print("\n📋 可用单位（按类别）：")
    for cat in ["length", "mass", "temperature", "pressure", "energy", "specific_energy",
                 "mass_flow", "density", "viscosity_dynamic", "ratio"]:
        units = list_available_units(category=cat)
        if units:
            names = [f"{u.symbol} ({u.name})" for u in units[:5]]
            more = f" +{len(units)-5}更多" if len(units) > 5 else ""
            print(f"  {cat:25s}: {', '.join(names)}{more}")

    print("\n" + "=" * 70)
    print("✅ A001 演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo()
