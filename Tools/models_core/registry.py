"""
ModelRegistry — 模型自动发现与注册
"""
from __future__ import annotations
import importlib
import pkgutil
import inspect
from typing import Dict, Optional, List, Type

from .base import BaseModelTool, ModelResult, InvocationContext


class ModelRegistry:
    """统一模型注册表，自动发现 models_core 包下的所有 BaseModelTool 子类"""

    def __init__(self):
        self._models: Dict[str, BaseModelTool] = {}
        self._initialized = False

    def discover(self, package_name: str = "models_core") -> int:
        """扫描当前包及子模块，注册所有 BaseModelTool 实例"""
        count = 0
        # 手动导入已知模块确保被发现
        for module_name in [
            "models_core.models_a",
            "models_core.models_b",
            "models_core.models_c",
        ]:
            try:
                importlib.import_module(module_name)
            except ImportError:
                continue

        # 扫描所有 BaseModelTool 子类
        for cls in self._find_subclasses(BaseModelTool):
            if cls.model_id:  # 只有设置了 model_id 的才注册
                instance = cls()
                self._models[cls.model_id] = instance
                count += 1

        self._initialized = True
        return count

    def _find_subclasses(self, base_cls: Type) -> List[Type]:
        """递归查找所有非抽象子类"""
        results = []
        for subclass in base_cls.__subclasses__():
            # 跳过基类自身（如果没设 model_id 就是抽象的）
            results.append(subclass)
            # 递归查找子类的子类
            results.extend(self._find_subclasses(subclass))
        return results

    def register(self, model: BaseModelTool) -> None:
        """手动注册一个模型实例"""
        self._models[model.model_id] = model

    def get(self, model_id: str) -> Optional[BaseModelTool]:
        """根据 model_id 获取模型实例"""
        if not self._initialized:
            self.discover()
        return self._models.get(model_id)

    def list_models(self) -> List[dict]:
        """返回所有注册模型的元数据列表"""
        if not self._initialized:
            self.discover()
        return [m.get_registry_entry() for m in self._models.values()]

    def list_by_scenario(self, scenario: str) -> List[dict]:
        """按场景筛选模型"""
        return [m.get_registry_entry() for m in self._models.values()
                if m.scenario == scenario]

    def invoke(self, model_id: str, params: dict,
               context: Optional[InvocationContext] = None) -> ModelResult:
        """调用模型：校验 + 执行"""
        model = self.get(model_id)
        if model is None:
            return ModelResult(
                success=False,
                error=f"未知模型 ID: {model_id}",
                error_code="UNKNOWN_MODEL",
            )

        # 输入校验
        errors = model.validate_input(params)
        if errors:
            return ModelResult(
                success=False,
                error="; ".join(errors),
                error_code="INVALID_INPUT",
            )

        # 执行
        return model.run_with_logging(params, context)


# 全局单例
registry = ModelRegistry()
