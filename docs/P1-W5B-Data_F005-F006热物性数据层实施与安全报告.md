# P1-W5B-Data：F005/F006热物性数据层实施与安全报告

日期：2026-08-26

分支：`main`

基线提交：`2e38c8e feat(tools): 新增F007结晶器热流工具至43项`

## 1. 本波结论

- 本波只建设F005/F006共用的数据层，不注册F005/F006，不增加工具数量。
- 当前严格计数仍为43个运行时工具、39个表格目录覆盖、43个完全合格工具。
- 新增2个批准物性集、15条热物性相关式、3条数学基准边界、3个F005解析/守恒基准算例。
- 运行时只读Repository只查询PostgreSQL批准记录，没有JSON或Python常量回退。
- 未导入DS042企业/实验室数据；没有用占位喷嘴、设备、浇次或传感器数据冒充生产数据。
- NIST 316L仅批准用于参考验证；不允许外推为其他钢种或用于生产控制。

## 2. 主工作簿约束复核

主目录 `绿色低碳冶金_数据库资料源与120小模型清单.xlsx` 的 `02_小模型清单120!A91:O93` 明确：

- F005是一维瞬态导热、潜热/等效比热数值工具，输入必须包含铸坯几何、拉速、边界热流和物性；输出包含坯壳厚度、温度场和能量残差。
- F006是F005下游的凝固终点事件定位/代理路径，不是F005改名包装。
- F007才是冷却水热平衡确定性公式工具。
- DS031/DS035/DS036/DS037分别是pycalphad、OpenFOAM、FiPy和FEniCSx求解框架，不能替代钢种热物性。
- DS042是受限内部数据，要求授权、脱敏、分级权限、数据字典和血缘；本波不导入。

## 3. 公开数据源审计

### 3.1 NIST SRM 1155a 316L

- 论文：Pichler, Simonds, Sowards and Pottlacher, *Measurements of thermophysical properties of solid and liquid NIST SRM 316L stainless steel*。
- DOI：`10.1007/s10853-019-04261-6`。
- 官方PDF：`https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=928362`。
- PDF SHA-256：`ae90ec5c55b1e4145ad8f70f3b77d3656ec6cbcc83c0684bc33e4cfef57266ff`。
- 许可：论文第12页明确为Creative Commons Attribution 4.0 International。
- 复核范围：表2、3、4、5、6、7均进行了文本提取与页面渲染目视核对。

入库内容：

- 表3固/液相密度多项式；
- 表6焓和体积修正电阻率离散表；
- 表7固相比热离散表；
- 1675 K固相线、1708 K液相线；
- 290 kJ/kg熔化潜热；
- 表4给出的测量不确定度与固/液相端点温度不确定度；
- 表5的SRM 1155a质量百分数组成。

所有入库量统一换算为SI单位，相关式保留原表号、来源类型、温区、相态、不确定度和记录自然键。

### 3.2 导热系数的明确限制

该论文没有直接测量导热系数。为使参考级PDE验证路径具备完整的 `rho/H/k` 数据，本波增加一个单独标识为 `DERIVED_MODEL_ESTIMATE` 的Wiedemann–Franz估算：

```text
k(T) = L0 * T / rho_electrical(T)
L0 = pi^2/3 * (k_B/e)^2 = 2.443004509073667e-8 W*ohm/K^2
```

- 电阻率来自论文表6的体积修正实测值并只做温区内线性插值。
- 该值不是论文直接测得的导热系数。
- 模型不确定度没有被来源论文建立，因此物性集使用域固定为 `REFERENCE_VALIDATION_ONLY`。
- 生产用途必须换用经过专业复核、设备/钢种匹配的批准物性集；不得静默使用此估算。

## 4. 新增数据库对象

迁移：`database/migrations/008_casting_thermal_property_data.sql`。

| 表 | 作用 | 本波行数 |
|---|---|---:|
| `metallurgy_v2.casting_material_property_set` | 物性集版本、钢种/组成、温区、固液相端点、许可与使用域 | 2 |
| `metallurgy_v2.casting_material_property_correlation` | 密度、焓、比热、导热、潜热、固相率等相关式及记录级来源 | 15 |
| `metallurgy_v2.casting_boundary_profile` | 带设备域、单位、符号约定和来源的边界曲线 | 3 |
| `metallurgy_v2.casting_model_benchmark_case` | 解析解、守恒恒等式的输入、期望值和容差 | 3 |

两个物性集：

1. `NIST_SRM1155A_316L_2019_V1`：公开NIST参考物性，验证用途；
2. `F005_ANALYTIC_CONSTANT_V1`：严格常物性数学介质，仅用于解析解/网格验证，不是钢种数据。

边界记录全部为数学基准：300 K定表温、零热流、100 kW/m2外向定热流。没有导入任何企业设备边界。

## 5. 安全导入与恢复证据

### 5.1 写入前基线

- PostgreSQL：17.10；工具路径：`D:/a_workplace/work_tools/PgSQL17/bin`。
- 写入前非系统表：24张。
- `metallurgy_v2.dataset_registry`：49行。
- `metallurgy_v2.dataset_import_run`：3行。

### 5.2 全库备份

- 文件：`backups/p1_w5b_data_20260826_172721/metallurgy_pre_w5b_data.dump`。
- 格式：PostgreSQL custom format，gzip压缩。
- 大小：756483 bytes。
- SHA-256：`4e1eeec0e351654cba0a68853ead1736dd88c664e2196fe8a46d3aa7f0ebad8b`。
- `pg_restore --list`成功读取208个TOC条目，备份和工具版本均为PostgreSQL 17.10。

### 5.3 恢复演练

- 临时库：`metallurgy_w5b_restore_20260826_172721`。
- 原库/恢复库均为24张非系统表。
- 逐表行数差异：零。
- 核验 `current_database()` 后仅删除该精确临时库；原库未被替换或清空。

### 5.4 导入与幂等

- 写入前dry-run：25条将新增，事务回滚。
- 正式导入审计ID：`9475bc36-a1a0-4e43-a022-a3abc0ae3f78`。
- 正式导入：25条新增、0条不变、0条覆盖。
- 资产SHA-256：`c478458b8cfff105f1469d403b2e2e3332c3afffa70b8142d868f8c20f3db116`。
- 导入后dry-run：0条新增、25条不变，证明自然键幂等。
- importer遇到相同自然键但内容不同会抛出冲突并回滚，不执行覆盖。

### 5.5 非目标数据核对

写入后非系统表为28张，即只增加上述4张目标表。

- 旧表允许变化：`dataset_registry`增加2行，`dataset_import_run`增加1行；
- 其余全部旧表逐表行数与写入前一致；
- 非目标差异检查结果：`{}`；
- 迁移不包含 `DELETE FROM`、`TRUNCATE`、`DROP TABLE`、`DROP SCHEMA` 或 `UPDATE`。

## 6. 只读Repository行为

文件：`Tools/models_core/repositories/casting_thermal_repository.py`。

- `approved_property_set`：只读批准物性集并返回数据集与记录溯源；
- `property_value` / `property_bundle`：温区内求值，返回单位、相态、方程类型、来源类型和不确定度；
- `boundary_profile`：按批准域读取边界值和符号约定；
- `benchmark_cases`：读取F005批准基准算例；
- 缺记录返回 `MISSING_DATA`，已有属性但温区不覆盖返回 `OUT_OF_DOMAIN`；
- 禁止温区外插值，禁止JSON/常量静默回退。

NIST比热在1253 K至1350 K之间没有本波批准记录，查询会明确失败；未来F005首版将采用论文表6焓表的焓法求解，不得伪造该间隙比热。

## 7. 验证结果

新增数据资格测试：`Tools/tests/test_p1_w5b_casting_thermal_data.py`。

- 11项聚焦测试全部通过；
- NIST 500 K密度、1000 K焓、993 K比热、1690 K潜热与论文表值/相关式一致；
- Wiedemann–Franz导热由独立常数重新计算一致；
- 固相率在1675/1708 K边界为1/0，且随温度单调不增；
- 常物性集满足 `alpha=k/(rho*cp)=1e-4 m2/s`；
- Dirichlet/Neumann解析温度由 `erf` 和半无限体公式独立重算一致；
- 缺数据、温区间隙、边界曲线超域均明确失败；
- importer事务内复跑为25条全部不变。

全量结果：

- `python -m pytest Tools/tests -q`：152 passed；
- `python Tools/run_baseline_tests.py`：11 tests，OK；
- 43项工具严格资格计数保持不变。

现有警告均为pycalphad在NumPy 2.5下的已知弃用警告，没有新增失败。

## 8. 已知限制与下一步门槛

本波完成后仍没有F005运行时工具；这是有意的资格隔离，而不是Schema-only计数。

实施F005前必须继续满足：

1. 使用隐式Euler有限体积和Picard迭代，不降级为经验平方根包装器；
2. 首版NIST路径采用焓法，不能重复叠加表6焓跃迁与290 kJ/kg潜热；
3. 常物性解析、零热流、定热流、能量闭合、网格/时间步加密均通过；
4. SciPy版本写入依赖锁定并记录求解器版本；
5. 工具Schema显式要求物性集ID、边界来源、几何、时间/网格和固相率阈值；
6. 生产用途必须拒绝数学基准集和参考验证集，除非调用明确处于验证模式；
7. DS042只有取得授权、脱敏数据字典和设备配置后才能另行导入。

下一波应只实现F005（43→44），完成解析解、能量闭合、网格独立、数据库失败和逐工具强制function-call测试后停止，不提前实现F006。
