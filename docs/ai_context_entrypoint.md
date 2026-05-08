# AI 执行入口

## 1. 使用方式

当 AI/agent 执行本项目中的开发、重构、评审或方案落地任务时，应优先阅读本文件，再按本文件要求继续阅读其他文档。

本文件的作用是：
- 提供统一入口
- 避免遗漏关键规范文档
- 根据任务类型自动确定应补读哪些专题设计文档和任务方案文档

---

## 2. 默认必读文档

所有代码相关任务，默认必须先阅读：

1. `docs/project_coding_standards_agent.md`
2. `docs/project_coding_standards.md`

说明：
- `project_coding_standards_agent.md` 提供执行短规则
- `project_coding_standards.md` 提供完整项目级规范

---

## 3. 按任务类型追加阅读

### 3.1 涉及异常处理、错误映射、校验分层
额外阅读：
- `docs/exception_handling_design.md`
- `docs/exceptions_usage.md`

适用场景：
- 设计或修改异常分类
- 设计或修改错误码映射  
- 设计或修改 API 边界的异常处理
- 设计或修改模型层 / 业务层 / API 层的异常职责分工
- 实现新的数据模型校验逻辑
- 编写API边界层的类型检查

说明：
- `docs/exception_handling_design.md` 提供异常处理的架构设计
- `docs/exceptions_usage.md` 提供异常类的具体使用指南和最佳实践

---

### 3.2 涉及具体方案实现
额外阅读：
- `docs/plans/<对应方案文档>`

适用场景：
- 某个功能、协议、接口、fake API 的具体落地
- 某个已形成方案文档的实现任务
- 异常类相关实现（参考 `docs/plans/common/exceptions_design.md`）

说明：
- 如果 plan 文档已存在，必须阅读对应 plan 文档
- 不允许绕过具体方案文档，仅凭全局规范直接实现
- 异常相关任务必须参考 `docs/plans/common/exceptions_design.md`

---
  
### 3.3 涉及日志记录、调试信息、监控
额外阅读：
- `docs/logger_usage.md`

适用场景：
- 在新模块中添加日志记录功能
- 修改现有日志级别或格式
- 实现类中的日志功能
- 配置日志文件输出
- 调试信息记录和异常上下文记录

说明：
- `docs/logger_usage.md` 提供日志模块的完整使用指南和最佳实践
- 日志应与异常处理体系配合使用
- 遵循分层日志策略（API层、业务层等）

---

### 3.4 涉及数据模型、数据结构、规则配置、拼接方案
额外阅读：
- `docs/models_usage.md`（使用指南）

适用场景：
- 使用 TireStruct、SmallImage、BigImage 等数据类
- 使用 RuleConfig、RuleFeature、RuleScore 等规则类
- 需要理解 Pipeline 数据流转
- 运行时填充 evaluation

说明：
- 如果需要生成数据类代码，阅读 `docs/plans/models/dataclass_design.md`
- 如果只是使用数据类，阅读 `docs/models_usage.md`

---

### 3.5 涉及架构边界、模型/API 设计调整
额外阅读：
- 相关专题设计文档
- 相关 plan 文档

适用场景：
- 修改输入输出边界
- 修改模型责任边界
- 修改 API 层和下层职责分工
- 修改版本与协议设计

---

## 4. 文档优先级

发生冲突时，按以下优先级处理：

1. 当前任务对应的方案文档（`docs/plans/...`）
2. 对应专题设计文档（例如 `docs/exception_handling_design.md`）
3. 项目完整规范（`docs/project_coding_standards.md`）
4. agent 短版规范（`docs/project_coding_standards_agent.md`）

说明：
- agent 短版规范用于快速执行约束
- 完整规范用于提供正式边界与完整标准
- 专题设计文档用于细化某一类问题的统一处理方式
- 任务方案文档用于本次任务的直接执行依据

---

## 5. 执行要求

- 不允许遗漏默认必读文档。
- 如果任务命中某个专题设计范围，必须补读对应专题文档。
- 如果任务存在对应的方案文档，必须补读对应方案文档。
- 如果发现文档之间存在冲突，必须显式说明冲突点，不允许静默按个人理解处理。
- 如果发现文档内容不足以直接执行，应先补设计或提问，不要自行扩展未确认方案。

---

## 6. 推荐调用方式

### 6.1 普通代码任务
推荐至少引用：
- `@docs/ai_context_entrypoint.md`

### 6.2 复杂任务 / 架构敏感任务 / 多文件任务
推荐引用：
- `@docs/ai_context_entrypoint.md`
- `@docs/plans/<对应方案文档>`

说明：
- AI 应先从入口文档判断还需要补读哪些其他文档

---

## 7. 当前与 Fake Generation API 相关的建议入口

如果任务与 Fake Generation API 最新版本有关，应额外阅读：
- `docs/plans/FakeGenerationAPI_v3.md`

如果任务涉及异常分类、错误映射、边界校验，也应额外阅读：
- `docs/exception_handling_design.md`
- `docs/exceptions_usage.md`  
- `docs/plans/common/exceptions_design.md`

如果任务涉及日志记录、调试或监控，应额外阅读：
- `docs/logger_usage.md`

---

**文档结束**
