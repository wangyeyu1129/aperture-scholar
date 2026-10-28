# 运行说明与限制

配置优先级：显式 Settings 构造参数 > 环境变量 > .env > 默认值。
`aperture check` 仅验证配置，不验证供应商可用性。`init-db` 创建本地 schema；
`demo` 使用固定 synthetic:demo ID 幂等写入一篇合成论文，验证基础设施。

接入真实搜索示例（不需要接入整个推荐管线）：

```python
import httpx
from aperture_scholar.config import Settings
from aperture_scholar.bootstrap import build_database
from aperture_scholar.infrastructure.sqlite import SQLiteResponseCache
from aperture_scholar.infrastructure.semantic_scholar import SemanticScholarSource

settings = Settings()
cache = SQLiteResponseCache(build_database(settings))
with httpx.Client() as client:
    source = SemanticScholarSource(client, cache, settings.s2)
    papers = source.search("retrieval robustness", limit=10)
```

该调用会访问配置的外部 API。供应商 key 从 `.env` 读取，不能打印 Settings 中解密后的 key。
API 配额与阈值需要按实际账号和标注集调整。

SQLite 只面向单机起步。备份前使用 SQLite backup API，避免仅复制有活动 WAL 的主文件。
当前缓存不自动清理过期行，后续加维护命令。卡片按 ID 幂等保存，list_cards 返回历史全集，
当前没有 run_id 隔离、访问控制、数据保留或多人部署；生产化需补齐 ROADMAP 中条目。

CI 运行 lint、格式、类型、测试、schema 同步和构建。配置只授予 contents:read。
分支保护未自动设置，项目所有者可在后续协作时设置必过 CI 与审核。
