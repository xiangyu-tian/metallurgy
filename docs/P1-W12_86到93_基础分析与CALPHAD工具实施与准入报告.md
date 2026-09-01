# P1-W12：86→93 基础分析与 CALPHAD 工具实施与准入报告

## 1. 结论

P1-W12 已新增并认证 A009、A010、B020、B022、B023、B024、B025 共 7 项真实可执行工具。既有 86 项计算实现未修改，统一注册中心现报告：

| 指标 | 结果 |
| --- | ---: |
| `registered_count` | 93 |
| `qualified_executable_count` | 93 |
| `fully_eligible_count` | 93 |
| `catalog_coverage_count` | 75 |
| `data_required_count` | 32 |
| `data_qualified_count` | 32 |

120 项主目录同步为 `93 已实现 + 25 后续保留 + 2 新增替换 = 120`。本波未生成正式研究数据集、未调用外部大模型 API、未连接现场数据、未安装依赖、未迁移或写入数据库。

## 2. 新增工具与验证依据

| ID | 工具/API | 依据与独立验证 | 数据与关系 |
| --- | --- | --- | --- |
| A009 | 稳健异常值检测 / `metallurgy_detect_outliers` | Tukey IQR、MAD 修正 Z 分数；手算围栏；平移与正比例缩放不变性；恒定样本边界和零尺度失败 | 公式工具；补充 A004/A008，不替代训练分布 OOD 检测 |
| A010 | 标量测量模型不确定度传播 / `metallurgy_propagate_uncertainty` | JCGM GUM 一阶传播与固定种子 Monte Carlo；线性解析方差、协方差项、方差闭合和重复性 | 公式/数值工具；使用受限表达式 AST；未来 G010 是多工具编排层 |
| B020 | 二元相界保形插值 / `metallurgy_interpolate_binary_phase_boundary` | 分段线性与 Fritsch–Butland PCHIP；节点重现、直线恒等、单调无超调、权重平方和不确定度复算 | 调用方显式离散点；向 B019 提供相界；与 B027 的方程求边界形成真实重叠 |
| B022 | 多元多相 Gibbs 能最小化 / `metallurgy_minimize_multiphase_gibbs_energy` | 元素守恒约束最小化；纯相线性规划结果、理想混合解析物种比、元素残差和可行扰动验证 | 显式 Gibbs 模型；泛化 B014，与 B013 重叠，并作为 B023 的原理参考路径 |
| B023 | 钢系 CALPHAD 单状态平衡 / `metallurgy_calculate_calphad_equilibrium_state` | pycalphad 0.11.2；稳定相量和相组成闭合、有限化学势/Gibbs 能、批准数据库记录与 SHA-256 核验 | 只读使用 `DS_MATCALC_MC_FE_2059`；与 F001/F002/F004 输出粒度不同；向 B025 提供校验输入 |
| B024 | Scheil–Gulliver 微偏析路径 / `metallurgy_calculate_scheil_microsegregation` | scheil 0.3.0；温度/液相分数单调、逐点相量闭合、逐组元全路径守恒和富集倍数复算 | 依赖 B023 同一批准 TDB；与 F004 的凝固分数/端点工具形成目标和输出粒度重叠 |
| B025 | 相图热力学一致性校验 / `metallurgy_validate_phase_diagram_consistency` | Gibbs 相律、相区邻接、杠杆重构、最低 Gibbs 能；合法图零违规，构造违规被逐类识别 | 公式/规则工具；校验 B019、B022、B023 输出，不自行预测相图 |

每项都包含严格输入输出 Schema 与单位、适用域、失败模式、标准错误码、来源和版本、依赖与重叠关系；注册资格用例至少为 3 个正常和 2 个边界/失败。所有工具均通过统一注册、真实 HTTP function-call 端点和隔离的命名强制调用。

## 3. 数据与依赖

- 复用虚拟环境版本：NumPy 2.5.1、SciPy 1.18.1、pycalphad 0.11.2、scheil 0.3.0；`pip check` 无破损依赖。
- B023/B024 只读使用已批准资产 `MATCALC-MC_FE-2.059-PYCALPHAD`，数据库版本 `mc_fe_v2.059`，数据集 `DS_MATCALC_MC_FE_2059`。
- 每次成功执行返回 `metallurgy_v2.solidification_model_definition` 的记录级 provenance，并核对 TDB 哈希 `sha256:a8628b6e0cb117f31d8278d87545e2d29fea78c9573694d0c51f1c72e50ac5e3`。
- 本波没有数据库 DDL/DML、数据导入、模型权重下载或依赖安装。

## 4. 验收记录

| 验收项 | 结果 |
| --- | --- |
| 新增专项准入、数学性质、数据库 provenance、HTTP 与强制调用 | `10 passed` |
| 注册基线、数据资格、目录映射回归 | `21 passed` |
| Python 编译检查 | 通过 |
| 依赖完整性 `pip check` | `No broken requirements found` |
| 新增 JSON 资产解析 | 通过 |

强制调用样例位于 `Tools/benchmarks/llm_tool_call_cases_p1_w12.json`，每项恰好一个，明确标记为接口烟测而非正式研究数据集。测试使用本地隔离 HTTP 契约，不访问外部大模型提供商。

## 5. 未解决问题与风险

- pycalphad 在 NumPy 2.5.1 下会产生数组 `shape` 赋值弃用警告；当前不影响结果或准入，但后续升级 NumPy/pycalphad 时应优先消除。
- `mc_fe_v2.059` 的温区、组元和相集边界是硬适用域；扩展到其他合金体系或任意 TDB 必须另行进行许可、哈希、数据库记录和科学基准审查。
- B022 当前覆盖纯相与理想混合相；非理想 CALPHAD 模型由 B023 承担，不应把 B022 宣称为通用 CALPHAD 替代。
- B024 遵循 Scheil–Gulliver 假设，不含固态回扩散、宏观偏析或现场传热耦合；不能用于在线连铸质量预测。

## 6. 下一批候选与停止点

按主目录当前顺序，下一批候选为 C008 熔渣/钢液黏度估算、D018 吹氧制度离线优化、D019 合金加入优化；D020 可作为紧随其后的热平衡约束优化工具。建议先实施 C008，再以 D023、D002/D007/D016 等现有原子工具为基础依次建设 D019、D018、D020。

本波到此停止，不自动进入下一批。下一批开始前应重新确认主分支、用户未提交改动、候选科学边界和所需公开参数资产；如需要新增数据库记录、迁移或导入，先提交变更说明和备份/回滚方案。
