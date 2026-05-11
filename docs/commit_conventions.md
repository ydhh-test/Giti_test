# Commit 规范

本项目使用轻量版 Conventional Commits，提交信息使用中文描述。

## 格式

```text
<type>(<scope>): <summary>
```

示例：

```text
test(rule19): 增加执行器验收测试模板
fix(geometry): 支持仅刷新当前总分
docs(node): 补充节点规则评估说明
```

## Type

```text
feat      新功能
fix       修复问题
refactor  重构，不改变外部行为
test      新增或修改测试
docs      文档修改
chore     工程配置、依赖、脚本等杂项
style     格式调整，不影响逻辑
```

## Scope

scope 优先使用受影响的模块或规则名。

常用 scope：

```text
rule
rule19
runner
registry
node
geometry
stitching
scoring
models
api
docs
tests
```

## Summary

summary 使用中文，说明本次提交做了什么。

建议：

```text
test(rule19): 增加执行器验收测试模板
```

避免：

```text
test: 修改代码
fix: 修复问题
update: 更新
```

## 提交粒度

一次 commit 只做一类事情。

推荐拆分：

```text
test(rule19): 增加执行器验收测试模板
fix(geometry): 支持仅刷新当前总分
docs(node): 补充节点规则评估说明
```

不推荐把业务逻辑、测试、文档和格式调整全部混在一个提交里。
