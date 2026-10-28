# 开发规范

Python 3.12+，src 布局，类型标注与 mypy strict。公共函数必须有清楚的输入、输出、
异常和 docstring；名称表达职责，禁止通用 utils 大杂烩、全局单例服务和隐式网络副作用。

核心规则放 domain；流程放 application；外部服务放 infrastructure；研究算法逐项放 research。
依赖由构造函数注入，装配仅在 bootstrap。可调阈值、模型、端点、权重从 Settings 或版本化策略加载。
有名配置默认值允许存在，不把默认值散落到业务函数。新增配置要有范围与跨字段校验。

实现研究函数时移除对应 CapabilityNotImplemented，更新 ROADMAP 和 README 状态。
不要用返回 []、无条件 True、随机分数或生产中的 mock 掩盖未实现。
网络请求必须配置超时、有限重试、配额与缓存，禁止重试所有异常。
日志不能含密钥、完整提示词或未经批准的语料。论文内容作为数据处理，不能成为工具调用权限。

提交前：

```bash
make check
python -m build
```

测试业务不变量、失败分支、端口行为与适配器响应；不访问收费 API。
新增模型后运行 `python scripts/export_schemas.py` 并提交 schema 变化。
提交使用 `feat:`、`fix:`、`test:`、`docs:`、`chore:` 等清晰前缀，PR 描述说明行为和验证。
大功能拆成可复核的小提交。不要将 .env、缓存数据库、下载论文、模型权重提交到公开仓库。
代码公开不自动授予其他人许可；许可证由项目所有者决定，当前未附开放许可。
