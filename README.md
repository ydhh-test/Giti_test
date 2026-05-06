# giti-tire-ai-pattern

轮胎花纹 AI 模式生成项目。

## Pipeline 概览

| Pipeline | 输入 | 输出 | 说明 |
|----------|------|------|------|
| Pipeline-1 | 小图 + 规则配置 | 大图 | 小图拼接为大图 |
| Pipeline-2 | 大图 + 规则配置 | 大图 | 大图重新拼接 |
| Pipeline-3 | 大图 + 规则配置 | 大图（含评估） | 业务评分 |
| Pipeline-4 | 大图 + 规则配置 | 小图 | 大图拆分 |

## 文档入口

所有文档导航从 `docs/ai_context_entrypoint.md` 开始。

---

**分支：dev2，为工程化的后处理架构和实现**
