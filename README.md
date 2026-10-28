# Aperture Scholar

**从领域文献中寻找有证据的研究机会。**

Aperture 表达打开研究视野的窗口；Scholar 表达论文与科研场景。
这是一个面向逐步实现的 Python 面向对象工程骨架：接口和流程先稳定，再逐项补齐研究算法。
目前不是已具备真实科研推荐能力的成品，也不宣称已经达到生产可用状态。

## 快速开始

要求 Python 3.12+。在仓库根目录执行：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
python -m pip install -e . --no-deps
cp .env.example .env
aperture check
aperture init-db
aperture demo
make check
```

`demo` 只验证合成论文入库、相似度和去重，不调用网络或收费模型，不生成科研推荐。
`aperture run` 会明确返回未实现错误（退出码 2）；研究适配器尚未就绪，不会悄悄使用假数据。
`.env` 中使用 `APERTURE_` 前缀与 `__` 嵌套键覆盖配置，密钥不写进代码。
现有默认阈值均为待校准的起点，不能视作准确性保证。

## 结构

```text
src/aperture_scholar/
├── domain/           # 不可变领域对象、异常、证据与相似度规则
├── application/      # 端口、抽取重试、流水线编排、排序权重聚合
├── infrastructure/   # SQLite、Semantic Scholar HTTP 适配器
├── research/         # 四阶段研究算法的具名类与待实现函数
├── config.py         # 环境配置、边界验证、SecretStr
├── bootstrap.py      # 唯一依赖装配入口
└── cli.py            # 操作入口
config/               # 实验与人工评审策略模板
schemas/              # 从领域模型导出的 JSON Schema
scripts/              # 生成契约文件
tests/               # 单元、适配器、编排、架构边界测试
docs/                # 架构、接口实施清单、开发与运行说明
.github/              # CI、依赖更新、PR 模板
```

## 当前可用范围

| 能力 | 状态 |
|---|---|
| 不可变结构化模型、JSON Schema、配置校验 | 已实现 |
| 指定论文/章节的证据匹配、来源检查、有限重抽 | 已实现 |
| 余弦相似度、稳定批次去重、排序权重聚合 | 已实现 |
| SQLite 论文、卡片、TTL 响应缓存 | 已实现 |
| Semantic Scholar 元数据搜索、限速、有限重试、缓存 | 已实现；已做模拟 HTTP 测试，未做真实 API 验收 |
| 流水线编排及边界质量闸门 | 已实现；使用测试替身验证 |
| 种子扩展、GROBID、结构化 LLM、实体归一化 | 函数骨架 |
| 二部图、局限性聚类、合理性判定 | 函数骨架 |
| RAG 生成、三维评审修订、三层新颖性检查 | 函数骨架 |
| 三维瑞士赛、回溯/盲评/消融、可选 UI | 函数骨架 / 后续阶段 |

阅读 [架构](docs/ARCHITECTURE.md)、[逐函数实施清单](docs/ROADMAP.md)、
[开发规范](CONTRIBUTING.md) 和 [运行边界](docs/OPERATIONS.md)。
项目不附带论文原文、私有语料、真实凭据或自动实验执行能力。
