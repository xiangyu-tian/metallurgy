"""A001 单位换算 —— FastAPI 服务端

启动: uvicorn a001_api:app --reload --port 8000
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional

from a001_unit_conversion import convert_units, list_available_units, UnitCategory

app = FastAPI(title="A001 单位换算 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 请求/响应模型 ──

class ConvertRequest(BaseModel):
    value: float = Field(..., description="数值")
    source_unit: str = Field(..., min_length=1, max_length=50, description="源单位")
    target_unit: str = Field(..., min_length=1, max_length=50, description="目标单位")
    strict: bool = False


class ConvertResponse(BaseModel):
    success: bool
    value: float
    source_value: float
    source_unit: str
    target_unit: str
    conversion_factor: float
    category: str
    dimension: str
    warnings: List[dict] = []
    error: Optional[str] = None


class CategoryInfo(BaseModel):
    category: str
    units: list


# ── API 路由 ──

@app.get("/")
def root():
    """前端页面"""
    html_path = os.path.join(os.path.dirname(__file__), "a001_frontend.html")
    if os.path.exists(html_path):
        with open(html_path, encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return {"name": "A001 单位换算", "version": "1.0.0", "docs": "/docs"}


@app.post("/convert", response_model=ConvertResponse)
def convert(req: ConvertRequest):
    """执行单位换算"""
    r = convert_units(req.value, req.source_unit, req.target_unit, req.strict)
    return ConvertResponse(
        success=r.success,
        value=r.value,
        source_value=r.source_value,
        source_unit=r.source_unit,
        target_unit=r.target_unit,
        conversion_factor=r.conversion_factor,
        category=r.category,
        dimension=r.dimension,
        warnings=[{"field": w.field, "message": w.message, "level": w.level}
                   for w in r.warnings],
        error=r.error,
    )


@app.get("/units")
def units(category: Optional[str] = None):
    """列出可用单位"""
    entries = list_available_units(category)
    # 按类别分组
    groups = {}
    for u in entries:
        groups.setdefault(u.category, []).append({
            "symbol": u.symbol,
            "name": u.name,
            "aliases": u.aliases,
            "description": u.description,
        })

    # 所有可用类别
    all_categories = [
        {"key": c.value, "label": _cat_label(c)} for c in UnitCategory
    ]

    return {
        "categories": all_categories,
        "units_by_category": {k: v for k, v in sorted(groups.items())},
    }


def _cat_label(c: UnitCategory) -> str:
    labels = {
        "length": "长度", "mass": "质量", "time": "时间",
        "temperature": "温度", "amount": "物质的量",
        "volume": "体积", "pressure": "压力", "energy": "能量",
        "power": "功率", "force": "力", "density": "密度",
        "concentration": "浓度", "flow": "流量", "viscosity_dynamic": "动力黏度",
        "viscosity_kinematic": "运动黏度", "area": "面积",
        "velocity": "速度", "angle": "角度",
        "specific_energy": "比能", "thermal_conductivity": "导热系数",
        "heat_capacity": "热容", "ratio": "比率",
        "mass_flow": "质量流量", "dimensionless": "无量纲",
    }
    return labels.get(c.value, c.value)
