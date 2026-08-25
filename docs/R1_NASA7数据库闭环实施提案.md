# R1 NASA7数据库闭环实施提案

## 1. 状态与授权边界

- 状态：提案，未执行
- 前置阶段：R0已完成代码实现与HTTP验证
- 本提案不构成数据库写入授权
- 用户确认前不得登记数据集、插入NASA7记录、删除静态资产或改变B002生产执行路径

## 2. 已核实事实

### 当前数据库

2026-08-25只读查询：

- `metallurgy_v2.thermodynamic_correlation`：45条 `SHOMATE`、0条 `NASA7`；
- `dataset_registry`已有DS001 NIST Chemistry WebBook、DS002 NIST-JANAF、DS007 NIST-JARVIS；
- `thermodynamic_correlation.equation_type` 已支持 `NASA7`，R1预计不需要表结构迁移。

### 当前仓库资产

- 文件：`Tools/models_core/data/nasa7_gri30_v1.json`
- 资产ID：`NASA7-GRI30-SUBSET-V1`
- 物种：O2、N2、CO、CO2、H2、H2O，均为气相；
- 每个物种两个温区段，共12条待导入关联式；
- 温区：200–1000 K、1000–3500 K；
- SHA-256：`5ae89a7d6d1c2f5bcb25dcc78850b968d1b9f210ab49b56ca91405eeb23e3136`。

### 来源核验

- GRI-Mech官方热力学页面说明其热化学数据基于NASA-Lewis、Technion等标准数据库，并提供由多项式系数计算的物性表和引用：
  `https://combustion.berkeley.edu/gri-mech/new21/data/thermo_table.html`
- Cantera维护的 `gri30.yaml` 明确标记GRI-Mech 3.0、原始输入文件 `gri30_thermo.dat`、NASA7模型和200/1000/3500 K分段：
  `https://github.com/Cantera/cantera/blob/main/data/gri30.yaml`
- Cantera不是GRI-Mech原始机制数据的授权方。不能把Cantera软件许可证自动视为GRI-Mech数据再分发许可证。

**当前许可结论：原始GRI-Mech数据的再分发边界仍需人工核验。许可未核验前，R1必须停在提案状态。**

## 3. 拟登记的数据集记录

| 字段 | 拟值 |
|---|---|
| dataset_id | `DS_NASA7_GRI30` |
| name | `GRI-Mech 3.0 NASA7 thermodynamic subset` |
| category | `热力学关联式` |
| provider | `GRI-Mech project / source attribution retained` |
| license | **待核验，禁止使用UNKNOWN占位执行导入** |
| access_url | 官方GRI-Mech页面；同时记录转换校验来源Cantera gri30.yaml |
| ingestion_mode | `官方数据文件/版本化导入` |
| version | `GRI-Mech 3.0 (1999-07-30), subset-v1` |
| retrieved_at | 实际获取时间 |
| checksum | `sha256:5ae89...e3136` |
| owner | 待用户指定责任组 |
| security_level | `公开`，须以许可复核为前提 |
| quality_grade | 建议 `B`，完成原始文件逐项核验后再升为A |
| lineage_json | 原始文件→物种筛选→相态规范化→双温区拆分→系数复算 |

## 4. 拟导入记录契约

每条 `thermodynamic_correlation` 记录：

```json
{
  "species_id": "O2",
  "phase": "gas",
  "equation_type": "NASA7",
  "temperature_min_k": 200.0,
  "temperature_max_k": 1000.0,
  "reference_temperature_k": 298.15,
  "reference_pressure_pa": 101325,
  "coefficients": {
    "a1": 3.78245636,
    "a2": -0.00299673416,
    "a3": 0.00000984730201,
    "a4": -9.68129509e-9,
    "a5": 3.24372837e-12,
    "a6": -1063.94356,
    "a7": 3.65767573
  },
  "coefficient_units": {
    "temperature": "K",
    "Cp": "J/(mol*K)",
    "H": "kJ/mol",
    "S": "J/(mol*K)"
  },
  "source_id": "DS_NASA7_GRI30",
  "source_record_key": "O2:gas:low",
  "priority": 10,
  "quality_level": "B",
  "metadata": {
    "segment": "low",
    "temperature_mid_k": 1000.0,
    "coefficient_order": ["a1", "a2", "a3", "a4", "a5", "a6", "a7"]
  }
}
```

高温段使用相同物种和 `source_record_key={species}:gas:high`。1000 K两段均覆盖时，低温段priority为10、高温段priority为20，Repository按priority升序选择，与当前 `T <= Tmid` 使用低温段的约定一致。

## 5. 拟执行事务

正式执行前应生成参数化SQL，由导入器在一个事务中完成：

```sql
BEGIN;

-- 1. 核验dataset_id尚不存在；许可、责任人和来源URL均不得为空。
-- 2. INSERT dataset_registry 1行。
-- 3. 参数化INSERT thermodynamic_correlation 12行。
-- 4. 核验12行、6物种、每物种2段、source_record_key唯一。
-- 5. 对12段运行Cp/H/S复算并与导入源比较。

COMMIT;
```

不使用字符串拼接SQL。若目标库已存在同一 `source_record_key`，默认中止，不自动覆盖。需要更新时必须建立新数据版本或得到明确覆盖授权。

### 预计影响

| 对象 | 插入 | 更新 | 删除 |
|---|---:|---:|---:|
| `dataset_registry` | 1 | 0 | 0 |
| `thermodynamic_correlation` | 12 | 0 | 0 |
| 其他表 | 0 | 0 | 0 |

## 6. 回滚方案

仅回滚本数据集产生的记录：

```sql
BEGIN;

DELETE FROM metallurgy_v2.thermodynamic_correlation
WHERE source_id = 'DS_NASA7_GRI30';

DELETE FROM metallurgy_v2.dataset_registry
WHERE dataset_id = 'DS_NASA7_GRI30';

COMMIT;
```

执行删除前必须先只读核验目标行数严格为12和1；若存在其他表外键引用则停止，不使用级联删除。

## 7. Repository与B002整改

### 数据访问

- 数据库配置统一从环境变量读取；删除 `thermodynamic_repository.py` 中的硬编码IP、端口、库名和用户。
- 新增 `find_nasa7_correlation(species, phase, temperature)`。
- SQL必须限定 `equation_type='NASA7'`、`is_active=true`、温区和相态，并按priority排序。
- 返回dataset_id、表名、记录ID、source_record_key、数据版本、温区和来源。

### B002执行

- `data_access_mode` 改为 `database_repository`；
- 增加至少一个数据资格样例；
- 成功结果的provenance必须包含真实数据库记录ID；
- 无记录返回 `MISSING_DATA`；
- 数据库不可连接返回 `DATA_BACKEND_UNAVAILABLE`；
- 不允许生产执行回退JSON；JSON仅保留为导入原件和独立测试参考。

## 8. 验证矩阵

1. 数据集登记字段完整、checksum一致；
2. 12条记录、6物种、每物种2段；
3. 每段恰有a1–a7七个有限系数；
4. O2、N2、CO、CO2、H2、H2O在300、900、1000、1500、3000 K按适用段复算；
5. `G=H-TS`；
6. 1000 K选择低温段，分段点两侧Cp/H/S连续性在声明容差内；
7. B002结果与原始系数直接计算一致；
8. 临时删除或禁用测试记录后，B002返回 `MISSING_DATA`；
9. 断开测试数据库后，返回 `DATA_BACKEND_UNAVAILABLE`；
10. `/api/v1/tools`仅在B002数据资格通过后增加 `metallurgy_b002`。

## 9. 停止条件

- 无法确认GRI-Mech原始数据许可或归属；
- 本地JSON与选定官方原始文件任一系数不一致；
- 数据库现有同ID或同source_record_key记录不能安全区分；
- 需要表结构迁移；
- 导入后记录数、checksum或热物性复算不一致；
- Repository仍需硬编码连接参数或静默回退才能通过测试。

## 10. 请求确认内容

进入R1前需要用户明确确认：

1. 是否采用GRI-Mech 3.0作为B002的正式NASA7数据源；
2. 是否授权核验并登记其许可信息；
3. 是否授权向当前数据库插入1条dataset记录和12条correlation记录；
4. 数据库写入前是否需要先在独立测试schema演练；
5. BOF等后续数据集是否继续按相同“提案→许可核验→导入预检→授权写入”流程推进。
