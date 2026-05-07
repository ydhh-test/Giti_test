# giti-tire-ai-pattern

轮胎花纹 AI 模式生成项目。

## Pipeline 概览

| Pipeline | 输入 | 输出 | 说明 | 入口 |
|----------|------|------|------|------|
| Pipeline-1 | 小图s + 规则配置 | 大图（含打分） | 生成大图并打分 | generate_big_image_with_evaluation |
| Pipeline-2 | 大图（血缘属性） + 规则配置 | 大图 | 大图重新拼接 | stitch_big_image_by_lineage |
| Pipeline-3 | 大图 + 规则配置 | 大图 | 重新打分 | update_big_image_score |
| Pipeline-4 | 大图 + 规则配置 | 小图s | 大图拆分 | split_big_image_into_small |

## 文档入口

所有文档导航从 `docs/ai_context_entrypoint.md` 开始。

---

**分支：dev2，为工程化的后处理架构和实现**
