# 逐函数实施清单

每一项先实现最小可验证行为，再接入 `bootstrap.build_pipeline`。接口输入输出见
`application/ports.py` 与 `domain/models.py`，骨架函数 docstring 提供细化约束。

| ID | 文件/类.函数 | 实施内容与验收 |
|---|---|---|
| C01 | research/corpus.py · CorpusBuilder.build | 种子一/两跳、年份/关键词过滤、摘要向量范围过滤、论文 ID 去重；重复运行不重复入库 |
| C02 | CorpusBuilder.update | arXiv 增量与调度游标；可恢复、幂等 |
| E01 | research/extraction.py · GrobidParser.parse | PDF/TEI 章节解析，审稿独立来源，方法补送章节；稳定证据定位 |
| E02 | StructuredExtractor.extract | 小模型结构化输出、schema 校验、修复提示；与 ExtractionService 重试组合 |
| E03 | SemanticEntityNormalizer.normalize | Embedding 候选、同义裁决、canonical/alias 持久表；保留证据 IDs |
| E04 | research/embeddings.py · ScientificEmbeddings.embed | SPECTER2 或 API，模型版本、批处理、顺序一致、向量缓存 |
| G01 | research/gaps.py · BipartiteGapDiscovery.discover | canonical 聚类、边论文计数/年份、迁移/热度/活性信号、合理性闸门 |
| G02 | LimitationGapDiscovery.discover | 科研 embedding、HDBSCAN、来源权重、不同论文频次、已解决检查 |
| G03 | CompositeGapDiscovery.discover | 两策略合并、语义去重、分数标定、top-k |
| I01 | research/generation.py · RetrievalContext.retrieve | gap 相关摘要+局限性与邻接实体，控制上下文预算 |
| I02 | ProposalGenerator.generate | 结构化分步方法、实验、风险、多样性；携带已生成摘要 |
| I03 | CriteriaReviewer.review | 新颖/可行/清晰三类固定 criteria，独立结构化意见 |
| I04 | CriteriaReviewer.revise | 有界修订，保留 idea/gap ID 与版本链 |
| N01 | research/novelty.py · ThreeLayerNoveltyChecker.check | 多查询+推荐扩展→向量粗筛→四档语义裁决；有界改写与可审计证据 |
| R01 | research/ranking.py · SwissTournamentRanker.rank | 三维独立比赛、避免重复对阵、公平 bye、位置偏差控制、确定性 tie-break |
| V01 | research/evaluation.py · TemporalBacktest.evaluate | 冻结历史语料和检索源，标注匹配对，命中率与置信区间 |
| V02 | BlindReviewExporter.export | 系统/直接生成对照，盲化随机化，单独保留映射 |
| V03 | AblationRunner.run | 同语料/预算/随机种子，移除 gap/review/novelty 分别评估 |

## 建议实现顺序

1. E01/E02 + C01：300 篇以内，人工核对 30 篇证据，抽取结构化库可检查。
2. E03 + G01/G02/G03：先检查实体与空白矩阵，再考虑生成。
3. I01/I02 + N01：先让带差异说明的候选卡片正确流转。
4. I03/I04 + R01：以消融证据决定迭代次数和排序策略。
5. V01/V02/V03 + 可选 Streamlit：用回溯和人评证明效果。

## 生产化前补齐

持久化 extraction/canonical/gap/review/run/feedback 表及迁移、作业断点/重放、
结构化日志与 run_id、token/费用预算、密钥管理、跨 worker 限速、可观测性、
提示词/模型版本化、超时/取消、数据保留策略、部署权限与备份恢复验收。
当前只提供这些能力的演进边界，避免过早引入微服务和任务队列。
