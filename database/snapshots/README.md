# 数据库交接快照

本目录保存 2026-09-09 导出的 PostgreSQL 17 数据库快照，编码为 UTF-8。

## 快照内容

### `metallurgy_public_20260909.sql.gz`

业务数据库 `metallurgy` 的可公开交接版本，包含完整表结构、模型基础数据、专业数据、基准数据和数据集登记信息。

为防止账号信息和实验输入进入公开 GitHub 仓库，以下表只保留结构，不包含数据：

- `User.accounts`
- `metallurgy_v2.experiment_run`
- `metallurgy_v2.invocation_logs`
- `metallurgy_v2.llm_tool_trace`
- `metallurgy_v2.model_execution_log`

恢复验证结果：60 个数据集、1,898 条热力学物性数据；上述敏感表均为空。

### `metallurgy_literature_20260909.sql.gz`

文献数据库 `metallurgy_literature` 的完整数据快照，包含：

- 348 篇文献
- 1,236 名作者
- 625 个关键词
- 348 条附件记录
- 文献与作者、领域、关键词之间的关联数据

附件表当前保存的是公开访问链接，没有本地 PDF 文件，因此本目录不包含 PDF 实体文件。

## 恢复方法

先解压 `.sql.gz` 文件，再恢复到一个新建的空数据库中。以文献库为例：

```powershell
createdb -U postgres metallurgy_literature
psql -U postgres -d metallurgy_literature -v ON_ERROR_STOP=1 -f metallurgy_literature_20260909.sql
```

业务数据库同理，建议恢复到名为 `metallurgy` 的空数据库。

快照不包含 PostgreSQL 用户、密码或服务器配置。数据库连接信息应通过部署环境变量单独配置。

## 文件校验

| 文件 | 大小（字节） | SHA-256 |
| --- | ---: | --- |
| `metallurgy_public_20260909.sql.gz` | 68,107 | `02365aa32d2f642e9aa3fbba638dc136e2d8c0b5a28d77fd4d4c01c74fad9d3b` |
| `metallurgy_literature_20260909.sql.gz` | 249,135 | `c81542a4d951386bc0a46be38c2625ef4ff9a4ff135be52d5993178a8d6161e6` |

两个快照均已执行实际恢复测试，并通过 API Key、Bearer Token、私钥和凭证参数特征扫描。
