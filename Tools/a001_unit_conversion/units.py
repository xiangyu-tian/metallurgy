"""
单位注册表 —— 量纲分析 + 冶金相关单位覆盖。

量纲系统（7个基本量纲）:
  L=长度, M=质量, T=时间, Θ=温度, N=物质量, I=电流, J=光强

对于冶金场景，常用量纲组合：
  压力   M·L⁻¹·T⁻²
  能量   M·L²·T⁻²
  功率   M·L²·T⁻³
  密度   M·L⁻³
  黏度   M·L⁻¹·T⁻¹
  流速   L³·T⁻¹
  力     M·L·T⁻²
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class UnitCategory(str, Enum):
    """单位类别 —— 按物理量分组"""
    LENGTH = "length"
    MASS = "mass"
    TIME = "time"
    TEMPERATURE = "temperature"
    AMOUNT = "amount"
    VOLUME = "volume"
    PRESSURE = "pressure"
    ENERGY = "energy"
    POWER = "power"
    FORCE = "force"
    DENSITY = "density"
    CONCENTRATION = "concentration"
    FLOW = "flow"
    VISCOSITY_DYNAMIC = "viscosity_dynamic"
    VISCOSITY_KINEMATIC = "viscosity_kinematic"
    AREA = "area"
    VELOCITY = "velocity"
    ANGLE = "angle"
    DIMENSIONLESS = "dimensionless"
    MASS_FLOW = "mass_flow"           # 质量流量（冶金过程重要）
    SPECIFIC_ENERGY = "specific_energy"  # 比能（J/kg, kWh/t 等）
    THERMAL_CONDUCTIVITY = "thermal_conductivity"  # 导热系数 W/(m·K)
    HEAT_CAPACITY = "heat_capacity"    # 热容 J/(kg·K), J/(mol·K)
    RATIO = "ratio"                    # 比率（%）, wt%, mol%


# 量纲向量: [L, M, T, Θ, N, I, J]
Dimension = Tuple[int, int, int, int, int, int, int]

# 维度模板
DIM_LENGTH: Dimension = (1, 0, 0, 0, 0, 0, 0)
DIM_MASS: Dimension = (0, 1, 0, 0, 0, 0, 0)
DIM_TIME: Dimension = (0, 0, 1, 0, 0, 0, 0)
DIM_TEMP: Dimension = (0, 0, 0, 1, 0, 0, 0)
DIM_AMOUNT: Dimension = (0, 0, 0, 0, 1, 0, 0)
DIM_AREA: Dimension = (2, 0, 0, 0, 0, 0, 0)
DIM_VOLUME: Dimension = (3, 0, 0, 0, 0, 0, 0)
DIM_VELOCITY: Dimension = (1, 0, -1, 0, 0, 0, 0)
DIM_ACCELERATION: Dimension = (1, 0, -2, 0, 0, 0, 0)
DIM_FORCE: Dimension = (1, 1, -2, 0, 0, 0, 0)
DIM_PRESSURE: Dimension = (-1, 1, -2, 0, 0, 0, 0)
DIM_ENERGY: Dimension = (2, 1, -2, 0, 0, 0, 0)
DIM_POWER: Dimension = (2, 1, -3, 0, 0, 0, 0)
DIM_DENSITY: Dimension = (-3, 1, 0, 0, 0, 0, 0)
DIM_CONCENTRATION_MOLAR: Dimension = (-3, 0, 0, 0, 1, 0, 0)
DIM_FLOW: Dimension = (3, 0, -1, 0, 0, 0, 0)
DIM_MASS_FLOW: Dimension = (0, 1, -1, 0, 0, 0, 0)
DIM_VISCOSITY_DYNAMIC: Dimension = (-1, 1, -1, 0, 0, 0, 0)
DIM_VISCOSITY_KINEMATIC: Dimension = (2, 0, -1, 0, 0, 0, 0)
DIM_SPECIFIC_ENERGY: Dimension = (2, 0, -2, 0, 0, 0, 0)
DIM_THERMAL_CONDUCTIVITY: Dimension = (1, 1, -3, -1, 0, 0, 0)
DIM_HEAT_CAPACITY_SPECIFIC: Dimension = (2, 0, -2, -1, 0, 0, 0)
DIM_HEAT_CAPACITY_MOLAR: Dimension = (2, 0, -2, -1, -1, 0, 0)
DIM_DIMENSIONLESS: Dimension = (0, 0, 0, 0, 0, 0, 0)
DIM_ANGLE: Dimension = (0, 0, 0, 0, 0, 0, 0)


@dataclass(frozen=True)
class UnitDef:
    """单个单位的定义"""
    name: str                    # 完整名称（如 "meter"）
    symbol: str                  # 符号（如 "m"）
    category: UnitCategory       # 物理量类别
    dimension: Dimension         # 量纲向量
    to_si_factor: float          # 乘以该因子得 SI 基值
    to_si_offset: float = 0.0    # 加该偏移得 SI 基值（仅温度类）
    aliases: List[str] = field(default_factory=list)  # 别名
    min_value: Optional[float] = None   # 合理最小值（SI 单位制下）
    max_value: Optional[float] = None   # 合理最大值（SI 单位制下）
    description: str = ""        # 简要说明


# ──────────────────────────────────────────────
# 单位注册表
# ──────────────────────────────────────────────
_UNIT_REGISTRY: Dict[str, UnitDef] = {}

# 用于按符号查找的二级索引
_SYMBOL_INDEX: Dict[str, str] = {}  # symbol -> name


def _register(u: UnitDef):
    """注册一个单位到全局注册表"""
    _UNIT_REGISTRY[u.name] = u
    _SYMBOL_INDEX[u.symbol] = u.name
    for alias in u.aliases:
        _SYMBOL_INDEX[alias] = u.name


# ─── 长度 Length ──────────────────────────────
_register(UnitDef("meter", "m", UnitCategory.LENGTH, DIM_LENGTH, 1.0,
                   aliases=["米", "公尺"], description="米，SI 基本长度单位"))
_register(UnitDef("kilometer", "km", UnitCategory.LENGTH, DIM_LENGTH, 1000.0,
                   aliases=["千米", "公里"], description="千米"))
_register(UnitDef("decimeter", "dm", UnitCategory.LENGTH, DIM_LENGTH, 0.1, description="分米"))
_register(UnitDef("centimeter", "cm", UnitCategory.LENGTH, DIM_LENGTH, 0.01,
                   aliases=["公分"], description="厘米"))
_register(UnitDef("millimeter", "mm", UnitCategory.LENGTH, DIM_LENGTH, 0.001,
                   aliases=["毫米"], description="毫米"))
_register(UnitDef("micrometer", "µm", UnitCategory.LENGTH, DIM_LENGTH, 1e-6,
                   aliases=["um", "micron", "微米", "μm"], description="微米"))
_register(UnitDef("nanometer", "nm", UnitCategory.LENGTH, DIM_LENGTH, 1e-9,
                   aliases=["纳米"], description="纳米"))
_register(UnitDef("inch", "in", UnitCategory.LENGTH, DIM_LENGTH, 0.0254,
                   aliases=["英寸", "\""], description="英寸"))
_register(UnitDef("foot", "ft", UnitCategory.LENGTH, DIM_LENGTH, 0.3048,
                   aliases=["英尺", "'"], description="英尺"))
_register(UnitDef("yard", "yd", UnitCategory.LENGTH, DIM_LENGTH, 0.9144,
                   aliases=["码"], description="码"))
_register(UnitDef("mile", "mi", UnitCategory.LENGTH, DIM_LENGTH, 1609.344,
                   aliases=["英里"], description="英里"))

# ─── 质量 Mass ────────────────────────────────
_register(UnitDef("kilogram", "kg", UnitCategory.MASS, DIM_MASS, 1.0,
                   aliases=["千克"], description="千克，SI 基本质量单位"))
_register(UnitDef("gram", "g", UnitCategory.MASS, DIM_MASS, 0.001,
                   aliases=["克"], description="克"))
_register(UnitDef("milligram", "mg", UnitCategory.MASS, DIM_MASS, 1e-6,
                   aliases=["毫克"], description="毫克"))
_register(UnitDef("metric_ton", "t", UnitCategory.MASS, DIM_MASS, 1000.0,
                   aliases=["tonne", "吨", "公吨"], description="公吨（1000 kg）"))
_register(UnitDef("pound", "lb", UnitCategory.MASS, DIM_MASS, 0.45359237,
                   aliases=["磅"], description="磅"))
_register(UnitDef("ounce", "oz", UnitCategory.MASS, DIM_MASS, 0.028349523125,
                   aliases=["盎司"], description="盎司"))
_register(UnitDef("us_ton", "us_ton", UnitCategory.MASS, DIM_MASS, 907.18474,
                   aliases=["short_ton", "美吨"], description="美吨（2000 lb）"))

# ─── 时间 Time ────────────────────────────────
_register(UnitDef("second", "s", UnitCategory.TIME, DIM_TIME, 1.0,
                   description="秒，SI 基本时间单位"))
_register(UnitDef("millisecond", "ms", UnitCategory.TIME, DIM_TIME, 0.001, description="毫秒"))
_register(UnitDef("microsecond", "µs", UnitCategory.TIME, DIM_TIME, 1e-6,
                   aliases=["us", "μs"], description="微秒"))
_register(UnitDef("minute", "min", UnitCategory.TIME, DIM_TIME, 60.0,
                   aliases=["分钟", "分"], description="分钟"))
_register(UnitDef("hour", "h", UnitCategory.TIME, DIM_TIME, 3600.0,
                   aliases=["hr", "小时", "时"], description="小时"))
_register(UnitDef("day", "d", UnitCategory.TIME, DIM_TIME, 86400.0,
                   aliases=["天", "日"], description="天"))

# ─── 温度 Temperature（含偏移量）─────────────
_register(UnitDef("kelvin", "K", UnitCategory.TEMPERATURE, DIM_TEMP, 1.0,
                   aliases=["开尔文"],
                   min_value=0.0,
                   description="开尔文，SI 基本温度单位"))
_register(UnitDef("celsius", "°C", UnitCategory.TEMPERATURE, DIM_TEMP, 1.0,
                   to_si_offset=273.15, aliases=["C", "degC", "摄氏度", "℃"],
                   min_value=-273.15,
                   description="摄氏度"))
_register(UnitDef("fahrenheit", "°F", UnitCategory.TEMPERATURE, DIM_TEMP, 5.0/9.0,
                   to_si_offset=459.67 * 5.0 / 9.0, aliases=["F", "degF", "华氏度"],
                   min_value=-459.67,
                   description="华氏度"))
_register(UnitDef("rankine", "°R", UnitCategory.TEMPERATURE, DIM_TEMP, 5.0/9.0,
                   to_si_offset=0.0, aliases=["R", "degR", "兰氏度"],
                   min_value=0.0,
                   description="兰氏度"))

# ─── 物质的量 Amount of substance ────────────
_register(UnitDef("mole", "mol", UnitCategory.AMOUNT, DIM_AMOUNT, 1.0,
                   aliases=["摩尔"], description="摩尔，SI 基本物质量单位"))
_register(UnitDef("kilomole", "kmol", UnitCategory.AMOUNT, DIM_AMOUNT, 1000.0,
                   aliases=["千摩尔"], description="千摩尔"))

# ─── 面积 Area ────────────────────────────────
_register(UnitDef("square_meter", "m²", UnitCategory.AREA, DIM_AREA, 1.0,
                   aliases=["m2", "sq_m", "平方米"], description="平方米"))
_register(UnitDef("square_centimeter", "cm²", UnitCategory.AREA, DIM_AREA, 1e-4,
                   aliases=["cm2", "sq_cm", "平方厘米"], description="平方厘米"))
_register(UnitDef("square_millimeter", "mm²", UnitCategory.AREA, DIM_AREA, 1e-6,
                   aliases=["mm2", "sq_mm", "平方毫米"], description="平方毫米"))
_register(UnitDef("square_inch", "in²", UnitCategory.AREA, DIM_AREA, 0.00064516,
                   aliases=["in2", "sq_in", "平方英寸"], description="平方英寸"))
_register(UnitDef("square_foot", "ft²", UnitCategory.AREA, DIM_AREA, 0.09290304,
                   aliases=["ft2", "sq_ft", "平方英尺"], description="平方英尺"))

# ─── 体积 Volume ──────────────────────────────
_register(UnitDef("cubic_meter", "m³", UnitCategory.VOLUME, DIM_VOLUME, 1.0,
                   aliases=["m3", "立方米"], description="立方米"))
_register(UnitDef("liter", "L", UnitCategory.VOLUME, DIM_VOLUME, 0.001,
                   aliases=["l", "dm3", "升", "立方分米", "公升"],
                   description="升"))
_register(UnitDef("milliliter", "mL", UnitCategory.VOLUME, DIM_VOLUME, 1e-6,
                   aliases=["ml", "cm3", "cc", "毫升"], description="毫升"))
_register(UnitDef("cubic_foot", "ft³", UnitCategory.VOLUME, DIM_VOLUME, 0.028316846592,
                   aliases=["ft3", "立方英尺"], description="立方英尺"))
_register(UnitDef("us_gallon", "gal", UnitCategory.VOLUME, DIM_VOLUME, 0.003785411784,
                   aliases=["gallon", "美加仑"], description="美制加仑"))
_register(UnitDef("barrel", "bbl", UnitCategory.VOLUME, DIM_VOLUME, 0.158987294928,
                   aliases=["桶"], description="石油桶（42 US gal）"))

# ─── 压力 Pressure ────────────────────────────
_register(UnitDef("pascal", "Pa", UnitCategory.PRESSURE, DIM_PRESSURE, 1.0,
                   min_value=0.0,
                   description="帕斯卡，SI 压力单位"))
_register(UnitDef("kilopascal", "kPa", UnitCategory.PRESSURE, DIM_PRESSURE, 1000.0,
                   description="千帕"))
_register(UnitDef("megapascal", "MPa", UnitCategory.PRESSURE, DIM_PRESSURE, 1e6,
                   description="兆帕"))
_register(UnitDef("gigapascal", "GPa", UnitCategory.PRESSURE, DIM_PRESSURE, 1e9,
                   description="吉帕"))
_register(UnitDef("bar", "bar", UnitCategory.PRESSURE, DIM_PRESSURE, 1e5,
                   aliases=["巴"], description="巴"))
_register(UnitDef("millibar", "mbar", UnitCategory.PRESSURE, DIM_PRESSURE, 100.0,
                   aliases=["毫巴"], description="毫巴"))
_register(UnitDef("atmosphere", "atm", UnitCategory.PRESSURE, DIM_PRESSURE, 101325.0,
                   aliases=["标准大气压"], description="标准大气压"))
_register(UnitDef("torr", "Torr", UnitCategory.PRESSURE, DIM_PRESSURE, 133.322368421,
                   aliases=["mmHg", "托"], description="托（毫米汞柱）"))
_register(UnitDef("psi", "psi", UnitCategory.PRESSURE, DIM_PRESSURE, 6894.757293168,
                   aliases=["lb_per_sq_in", "磅每平方英寸"],
                   description="磅力每平方英寸"))
_register(UnitDef("mm_h2o", "mmH₂O", UnitCategory.PRESSURE, DIM_PRESSURE, 9.80665,
                   aliases=["mmH2O", "毫米水柱"], description="毫米水柱"))

# ─── 能量 Energy ──────────────────────────────
_register(UnitDef("joule", "J", UnitCategory.ENERGY, DIM_ENERGY, 1.0,
                   min_value=0.0,
                   description="焦耳，SI 能量单位"))
_register(UnitDef("kilojoule", "kJ", UnitCategory.ENERGY, DIM_ENERGY, 1000.0,
                   description="千焦"))
_register(UnitDef("megajoule", "MJ", UnitCategory.ENERGY, DIM_ENERGY, 1e6, description="兆焦"))
_register(UnitDef("gigajoule", "GJ", UnitCategory.ENERGY, DIM_ENERGY, 1e9, description="吉焦"))
_register(UnitDef("calorie", "cal", UnitCategory.ENERGY, DIM_ENERGY, 4.184,
                   aliases=["卡"], description="热化学卡路里"))
_register(UnitDef("kilocalorie", "kcal", UnitCategory.ENERGY, DIM_ENERGY, 4184.0,
                   aliases=["千卡", "大卡"], description="千卡"))
_register(UnitDef("watt_hour", "Wh", UnitCategory.ENERGY, DIM_ENERGY, 3600.0,
                   aliases=["瓦时"], description="瓦时"))
_register(UnitDef("kilowatt_hour", "kWh", UnitCategory.ENERGY, DIM_ENERGY, 3.6e6,
                   aliases=["千瓦时", "度"], description="千瓦时"))
_register(UnitDef("megawatt_hour", "MWh", UnitCategory.ENERGY, DIM_ENERGY, 3.6e9,
                   description="兆瓦时"))
_register(UnitDef("btu", "BTU", UnitCategory.ENERGY, DIM_ENERGY, 1055.05585262,
                   aliases=["英热单位"], description="英热单位"))
_register(UnitDef("electronvolt", "eV", UnitCategory.ENERGY, DIM_ENERGY, 1.602176634e-19,
                   description="电子伏特"))

# ─── 功率 Power ───────────────────────────────
_register(UnitDef("watt", "W", UnitCategory.POWER, DIM_POWER, 1.0,
                   min_value=0.0,
                   description="瓦特，SI 功率单位"))
_register(UnitDef("kilowatt", "kW", UnitCategory.POWER, DIM_POWER, 1000.0, description="千瓦"))
_register(UnitDef("megawatt", "MW", UnitCategory.POWER, DIM_POWER, 1e6, description="兆瓦"))
_register(UnitDef("gigawatt", "GW", UnitCategory.POWER, DIM_POWER, 1e9, description="吉瓦"))
_register(UnitDef("horsepower", "hp", UnitCategory.POWER, DIM_POWER, 745.699871582,
                   aliases=["马力"], description="英制马力"))

# ─── 力 Force ─────────────────────────────────
_register(UnitDef("newton", "N", UnitCategory.FORCE, DIM_FORCE, 1.0,
                   description="牛顿，SI 力单位"))
_register(UnitDef("kilonewton", "kN", UnitCategory.FORCE, DIM_FORCE, 1000.0, description="千牛"))
_register(UnitDef("lbf", "lbf", UnitCategory.FORCE, DIM_FORCE, 4.4482216152605,
                   aliases=["磅力"], description="磅力"))
_register(UnitDef("dyne", "dyn", UnitCategory.FORCE, DIM_FORCE, 1e-5, description="达因"))

# ─── 密度 Density ─────────────────────────────
_register(UnitDef("kg_per_cubic_meter", "kg/m³", UnitCategory.DENSITY, DIM_DENSITY, 1.0,
                   aliases=["kg/m3", "kg_per_m3"], description="千克每立方米 (SI)"))
_register(UnitDef("g_per_cubic_cm", "g/cm³", UnitCategory.DENSITY, DIM_DENSITY, 1000.0,
                   aliases=["g/cm3", "g_per_cm3", "克每立方厘米"],
                   description="克每立方厘米（数值=水的密度）"))
_register(UnitDef("kg_per_liter", "kg/L", UnitCategory.DENSITY, DIM_DENSITY, 1000.0,
                   aliases=["kg/l", "kg_per_l"], description="千克每升"))
_register(UnitDef("lb_per_cubic_foot", "lb/ft³", UnitCategory.DENSITY, DIM_DENSITY, 16.018463374,
                   aliases=["lb/ft3", "lb_per_ft3"], description="磅每立方英尺"))

# ─── 浓度 Concentration ───────────────────────
_register(UnitDef("mol_per_cubic_meter", "mol/m³", UnitCategory.CONCENTRATION, DIM_CONCENTRATION_MOLAR, 1.0,
                   aliases=["mol/m3"], description="摩尔每立方米 (SI)"))
_register(UnitDef("mol_per_liter", "mol/L", UnitCategory.CONCENTRATION, DIM_CONCENTRATION_MOLAR, 1000.0,
                   aliases=["M", "mol/l", "mol_per_l", "摩尔每升"],
                   description="摩尔每升（物质的量浓度）"))
_register(UnitDef("percent", "%", UnitCategory.RATIO, DIM_DIMENSIONLESS, 0.01,
                   aliases=["pct", "百分"], description="百分比"))
_register(UnitDef("ppm", "ppm", UnitCategory.RATIO, DIM_DIMENSIONLESS, 1e-6,
                   aliases=["parts_per_million", "百万分率"],
                   min_value=0.0,
                   description="百万分率"))
_register(UnitDef("ppb", "ppb", UnitCategory.RATIO, DIM_DIMENSIONLESS, 1e-9,
                   aliases=["parts_per_billion", "+亿分率"]))
_register(UnitDef("wt_percent", "wt%", UnitCategory.RATIO, DIM_DIMENSIONLESS, 0.01,
                   aliases=["质量分数", "质量百分比"], description="质量百分比"))
_register(UnitDef("mass_ppm", "mass_ppm", UnitCategory.RATIO, DIM_DIMENSIONLESS, 1e-6,
                   description="质量百万分率（= ppm）"))

# ─── 流速 Volumetric Flow ─────────────────────
_register(UnitDef("cubic_meter_per_second", "m³/s", UnitCategory.FLOW, DIM_FLOW, 1.0,
                   aliases=["m3/s"], description="立方米每秒 (SI)"))
_register(UnitDef("liter_per_minute", "L/min", UnitCategory.FLOW, DIM_FLOW, 0.001 / 60.0,
                   aliases=["lpm", "l/min", "升每分钟"], description="升每分钟"))
_register(UnitDef("cubic_meter_per_hour", "m³/h", UnitCategory.FLOW, DIM_FLOW, 1.0/3600.0,
                   aliases=["m3/h", "立方米每小时"], description="立方米每小时"))
_register(UnitDef("gallon_per_minute", "gpm", UnitCategory.FLOW, DIM_FLOW, 0.0000630901964,
                   aliases=["gal/min", "美加仑每分钟"], description="美加仑每分钟"))

# ─── 质量流量 Mass Flow ───────────────────────
_register(UnitDef("kg_per_second", "kg/s", UnitCategory.MASS_FLOW, DIM_MASS_FLOW, 1.0,
                   aliases=["千克每秒"], description="千克每秒 (SI)"))
_register(UnitDef("ton_per_hour", "t/h", UnitCategory.MASS_FLOW, DIM_MASS_FLOW, 1000.0/3600.0,
                   aliases=["吨每小时"], description="吨每小时（冶金常用）"))
_register(UnitDef("kg_per_minute", "kg/min", UnitCategory.MASS_FLOW, DIM_MASS_FLOW, 1.0/60.0,
                   aliases=["千克每分钟"], description="千克每分钟"))
_register(UnitDef("ton_per_day", "t/d", UnitCategory.MASS_FLOW, DIM_MASS_FLOW, 1000.0/86400.0,
                   aliases=["吨每天"], description="吨每天"))

# ─── 速度 Velocity ────────────────────────────
_register(UnitDef("meter_per_second", "m/s", UnitCategory.VELOCITY, DIM_VELOCITY, 1.0,
                   aliases=["米每秒"], description="米每秒 (SI)"))
_register(UnitDef("km_per_hour", "km/h", UnitCategory.VELOCITY, DIM_VELOCITY, 1000.0/3600.0,
                   aliases=["kph", "千米每小时", "公里每小时"], description="千米每小时"))
_register(UnitDef("foot_per_second", "ft/s", UnitCategory.VELOCITY, DIM_VELOCITY, 0.3048,
                   aliases=["英尺每秒"], description="英尺每秒"))
_register(UnitDef("mile_per_hour", "mph", UnitCategory.VELOCITY, DIM_VELOCITY, 0.44704,
                   aliases=["英里每小时"], description="英里每小时"))

# ─── 黏度 Viscosity ───────────────────────────
# 动力黏度
_register(UnitDef("pascal_second", "Pa·s", UnitCategory.VISCOSITY_DYNAMIC, DIM_VISCOSITY_DYNAMIC, 1.0,
                   aliases=["Pa s", "Pa*s"], min_value=0.0,
                   description="帕斯卡·秒 (SI)"))
_register(UnitDef("centipoise", "cP", UnitCategory.VISCOSITY_DYNAMIC, DIM_VISCOSITY_DYNAMIC, 0.001,
                   aliases=["厘泊"], min_value=0.0, description="厘泊"))
_register(UnitDef("poise", "P", UnitCategory.VISCOSITY_DYNAMIC, DIM_VISCOSITY_DYNAMIC, 0.1,
                   aliases=["泊"], min_value=0.0, description="泊"))

# 运动黏度
_register(UnitDef("square_meter_per_second", "m²/s", UnitCategory.VISCOSITY_KINEMATIC, DIM_VISCOSITY_KINEMATIC, 1.0,
                   aliases=["m2/s"], min_value=0.0,
                   description="平方米每秒 (SI)"))
_register(UnitDef("centistoke", "cSt", UnitCategory.VISCOSITY_KINEMATIC, DIM_VISCOSITY_KINEMATIC, 1e-6,
                   aliases=["厘斯"], min_value=0.0, description="厘斯"))
_register(UnitDef("stoke", "St", UnitCategory.VISCOSITY_KINEMATIC, DIM_VISCOSITY_KINEMATIC, 1e-4,
                   aliases=["斯托克斯"], min_value=0.0, description="斯托克斯"))

# ─── 比能 Specific Energy ─────────────────────
_register(UnitDef("joule_per_kg", "J/kg", UnitCategory.SPECIFIC_ENERGY, DIM_SPECIFIC_ENERGY, 1.0,
                   description="焦耳每千克 (SI)"))
_register(UnitDef("kWh_per_ton", "kWh/t", UnitCategory.SPECIFIC_ENERGY, DIM_SPECIFIC_ENERGY, 3600.0,
                   aliases=["千瓦时每吨"], description="千瓦时每吨（冶金能耗常用）"))
_register(UnitDef("MJ_per_ton", "MJ/t", UnitCategory.SPECIFIC_ENERGY, DIM_SPECIFIC_ENERGY, 1000.0,
                   description="兆焦每吨"))
_register(UnitDef("kJ_per_kg", "kJ/kg", UnitCategory.SPECIFIC_ENERGY, DIM_SPECIFIC_ENERGY, 1000.0,
                   description="千焦每千克"))

# ─── 热容 Heat Capacity ───────────────────────
_register(UnitDef("J_per_kg_K", "J/(kg·K)", UnitCategory.HEAT_CAPACITY, DIM_HEAT_CAPACITY_SPECIFIC, 1.0,
                   aliases=["J/(kg*K)"], description="焦每千克开 (SI)"))
_register(UnitDef("kJ_per_kg_K", "kJ/(kg·K)", UnitCategory.HEAT_CAPACITY, DIM_HEAT_CAPACITY_SPECIFIC, 1000.0,
                   aliases=["kJ/(kg*K)"], description="千焦每千克开"))
_register(UnitDef("J_per_mol_K", "J/(mol·K)", UnitCategory.HEAT_CAPACITY, DIM_HEAT_CAPACITY_MOLAR, 1.0,
                   aliases=["J/(mol*K)"], description="焦每摩尔开"))

# ─── 导热系数 Thermal Conductivity ────────────
_register(UnitDef("W_per_m_K", "W/(m·K)", UnitCategory.THERMAL_CONDUCTIVITY, DIM_THERMAL_CONDUCTIVITY, 1.0,
                   aliases=["W/(m*K)"], min_value=0.0,
                   description="瓦每米开 (SI)"))
_register(UnitDef("kcal_per_h_m_K", "kcal/(h·m·K)", UnitCategory.THERMAL_CONDUCTIVITY, DIM_THERMAL_CONDUCTIVITY, 1.16222222,
                   aliases=["千卡每小时米开"]))
_register(UnitDef("W_per_cm_K", "W/(cm·K)", UnitCategory.THERMAL_CONDUCTIVITY, DIM_THERMAL_CONDUCTIVITY, 100.0,
                   aliases=["W/(cm*K)"], description="瓦每厘米开"))


# ─── 辅助函数 ──────────────────────────────────

def resolve_unit(unit_str: str) -> Optional[UnitDef]:
    """通过符号或名称查找单位定义，大小写不敏感"""
    # 原始查找
    key = unit_str.strip()
    if key in _UNIT_REGISTRY:
        return _UNIT_REGISTRY[key]
    if key in _SYMBOL_INDEX:
        return _UNIT_REGISTRY[_SYMBOL_INDEX[key]]

    # 小写查找
    key_lower = key.lower()
    for name, u in _UNIT_REGISTRY.items():
        if name.lower() == key_lower:
            return u
        if u.symbol.lower() == key_lower:
            return u
        for alias in u.aliases:
            if alias.lower() == key_lower:
                return u

    return None


def get_units_by_category(cat: UnitCategory) -> List[UnitDef]:
    """获取指定类别的所有单位"""
    return [u for u in _UNIT_REGISTRY.values() if u.category == cat]


def dimensions_match(d1: Dimension, d2: Dimension) -> bool:
    """检查两个量纲是否一致"""
    return d1 == d2


def get_category_for_dimension(dim: Dimension) -> Optional[UnitCategory]:
    """根据量纲向量推断类别"""
    mapping = {
        DIM_LENGTH: UnitCategory.LENGTH,
        DIM_MASS: UnitCategory.MASS,
        DIM_TIME: UnitCategory.TIME,
        DIM_TEMP: UnitCategory.TEMPERATURE,
        DIM_AMOUNT: UnitCategory.AMOUNT,
        DIM_AREA: UnitCategory.AREA,
        DIM_VOLUME: UnitCategory.VOLUME,
        DIM_VELOCITY: UnitCategory.VELOCITY,
        DIM_FORCE: UnitCategory.FORCE,
        DIM_PRESSURE: UnitCategory.PRESSURE,
        DIM_ENERGY: UnitCategory.ENERGY,
        DIM_POWER: UnitCategory.POWER,
        DIM_DENSITY: UnitCategory.DENSITY,
        DIM_CONCENTRATION_MOLAR: UnitCategory.CONCENTRATION,
        DIM_FLOW: UnitCategory.FLOW,
        DIM_MASS_FLOW: UnitCategory.MASS_FLOW,
        DIM_VISCOSITY_DYNAMIC: UnitCategory.VISCOSITY_DYNAMIC,
        DIM_VISCOSITY_KINEMATIC: UnitCategory.VISCOSITY_KINEMATIC,
        DIM_SPECIFIC_ENERGY: UnitCategory.SPECIFIC_ENERGY,
        DIM_THERMAL_CONDUCTIVITY: UnitCategory.THERMAL_CONDUCTIVITY,
        DIM_DIMENSIONLESS: UnitCategory.DIMENSIONLESS,
    }
    return mapping.get(dim)


def dimension_symbol(dim: Dimension) -> str:
    """量纲的可读表示"""
    symbols = ["L", "M", "T", "Θ", "N", "I", "J"]
    parts = []
    for i, d in enumerate(dim):
        if d == 1:
            parts.append(symbols[i])
        elif d != 0:
            parts.append(f"{symbols[i]}^{d}")
    return "·".join(parts) if parts else "1"


__all__ = [
    "UnitDef", "UnitCategory", "Dimension",
    "resolve_unit", "get_units_by_category",
    "dimensions_match", "get_category_for_dimension",
    "dimension_symbol",
]
