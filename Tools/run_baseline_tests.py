"""运行不依赖 pytest 的 v2.0 基线与实验链路回归测试。"""

from __future__ import annotations

import os
import sys
import unittest


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)
sys.path.insert(0, PROJECT_DIR)

from tests import test_model_baseline, test_thermo_fallback


def main() -> int:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(test_model_baseline))
    suite.addTests(loader.loadTestsFromModule(test_thermo_fallback))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
