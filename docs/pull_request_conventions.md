# Pull Request 规范

本规范参考 GitHub 官方文档整理，用于统一本项目 PR 的标题、正文和
review 信息结构。

## 参考来源

- GitHub Docs: Creating a pull request
  https://docs.github.com/articles/creating-a-pull-request?tool=webui
- GitHub Docs: Creating a pull request template for your repository
  https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository
- GitHub Docs: Helping others review your changes
  https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/getting-started/helping-others-review-your-changes
- GitHub Docs: About pull request reviews
  https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews

## PR 标题

PR 标题沿用项目 commit 规范：

```text
<type>(<scope>): <summary>
```

示例：

```text
test(rule19): 增加执行器验收测试模板
fix(geometry): 支持仅刷新当前总分
docs(node): 补充节点规则评估说明
```

## PR 正文结构

建议 PR 正文包含以下章节：

````md
## 背景

说明为什么需要这个 PR。

## 修改内容

按模块列出主要改动。

## 验证方式

列出已经执行过的测试、检查命令和结果。

## 影响范围

说明影响哪些模块、是否改变默认行为、是否有兼容风险。

## Review 关注点

告诉 reviewer 希望重点看哪里。
```

## 本次 PR 草稿

### 标题

```text
test(rule): 增加 Rule19 验收测试并补充节点规则说明
```

### 正文

```md
## 背景

本次 PR 围绕 Rule 层对接和节点规则评估做整理，目标是让 Rule 的新增、
算法对接、Node 过滤关系都有更清晰的验收方式，同时补充项目内的提交规范文档。

## 修改内容

### Rule19 验收测试

- 新增 `tests/unittests/rules/executors/test_rule19_executor.py`
- 验证 `Rule19Executor` 可以通过 `Rule19Config.name` 从注册表读取
- 验证 `Rule19Config` 会被拼接方案生成节点的规则过滤选中
- 增加 `exec_feature` 算法对接占位测试
- 增加 `exec_score` 打分逻辑占位测试

### 几何评分节点

- 为 `score_geometry` 增加 `recalculate_rule_scores` 参数
- 默认保持重新计算规则分数
- 支持传入 `recalculate_rule_scores=False` 时只刷新 `current_score`
- 补充几何评分相关单元测试

### 文档说明

- 补充 Node 层 helper 和 evaluator 的中文说明
- 新增 `docs/commit_conventions.md`
- 明确项目 commit 格式、type、scope 和提交粒度

## 验证方式

已执行全量单元测试：

```bash
.\.venv\Scripts\python.exe -m pytest tests/unittests -q
```

结果：

```text
292 passed, 2 skipped, 27 subtests passed
```

补充执行语法检查：

```bash
.\.venv\Scripts\python.exe -m py_compile src/nodes/base.py src/nodes/big_image_evaluator.py src/nodes/small_image_evaluator.py
```

结果：通过，无编译错误。

## 影响范围

- 影响 Rule19 执行器验收测试组织方式
- 影响几何评分节点 `score_geometry`，但默认行为保持重新计算规则分数
- 新增仅刷新总分的可选能力
- 新增文档，不影响运行时逻辑

## Review 关注点

- Rule19 的验收测试是否足够覆盖后续算法对接场景
- Node 过滤验收是否适合放在 Rule 对应测试文件中维护
- `score_geometry(recalculate_rule_scores=False)` 的语义是否清晰
- commit 规范是否符合项目后续协作习惯
````
