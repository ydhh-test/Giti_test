<!--
Sync Impact Report
===================
Version: 1.1.0 | Sync Date: 2025-02-13 | Changes Detected: Git Commit Standards added

Template Updates Applied:
- ✅ .specify/templates/plan-template.md - Updated Python version example from 3.11 to 3.12
- ✅ .specify/templates/spec-template.md - Verified compatible with constitution
- ✅ .specify/templates/tasks-template.md - Added Git Commit Standards reference
- ✅ .specify/templates/checklist-template.md - Verified compatible with constitution
- ✅ .specify/templates/constitution-template.md - Verified compatible with constitution

Command Files Status:
- ✅ .claude/commands/speckit.specify.md - Added Git Commit Compliance section
- ✅ .claude/commands/speckit.plan.md - Added Git Commit Compliance section
- ✅ .claude/commands/speckit.tasks.md - Added Git Commit Compliance section
- ✅ .claude/commands/speckit.implement.md - Added Git Commit Compliance section
- ✅ .claude/commands/speckit.clarify.md - Added Git Commit Compliance section
- ✅ .claude/commands/speckit.analyze.md - Added Git Commit Compliance section
- ✅ .claude/commands/speckit.checklist.md - Added Git Commit Compliance section
- ✅ .claude/commands/speckit.taskstoissues.md - Added Git Commit Compliance section

Follow-up TODOs:
- None
-->

Added Sections:
- Core Principles: 6 principles defined
- Technical Standards
- Collaboration Workflow (including Git Commit Standards)
- AI Behavior Guidelines
- Delivery Standards

Removed Sections:
- N/A

Templates Requiring Updates:
- ✅ .specify/templates/plan-template.md - Technical Context section aligns with Python 3.12 + Conda requirement
- ✅ .specify/templates/spec-template.md - OpenAPI 3.0 compliance noted in Success Criteria guidelines
- ✅ .specify/templates/tasks-template.md - Git Commit Standards reference added
- ✅ .claude/commands/speckit.specify.md - Git Commit Compliance section added
- ✅ .claude/commands/speckit.plan.md - Git Commit Compliance section added
- ✅ .claude/commands/speckit.tasks.md - Git Commit Compliance section added
- ✅ .claude/commands/speckit.implement.md - Git Commit Compliance section added
- ✅ .claude/commands/speckit.clarify.md - Git Commit Compliance section added
- ✅ .claude/commands/speckit.analyze.md - Git Commit Compliance section added
- ✅ .claude/commands/speckit.checklist.md - Git Commit Compliance section added
- ✅ .claude/commands/speckit.taskstoissues.md - Git Commit Compliance section added

Follow-up TODOs:
- None
-->

# Giti Test Constitution

## Core Principles

### I. Project Goal

**项目目标**：统一项目规范，自动生成可落地的接口、代码与配置，提高研发效率。

**Rationale**: 明确项目的核心目标，确保所有开发工作围绕规范化和自动化展开，减少重复劳动，提升整体研发效率。

### II. Technical Principles

**技术原则**：使用 Python 3.12，Conda 环境，遵循 Spec-Kit 规范。

**具体要求**：
- 所有 Python 代码必须兼容 Python 3.12
- 使用 Conda 进行环境管理和依赖隔离
- 严格遵循 Spec-Kit 工作流（Constitution → Specify → Plan → Tasks → Implement）
- 技术选型必须经过技术方案（plan.md）论证

**Rationale**: 统一技术栈版本和环境管理方式，确保代码可重复构建和环境一致性。

### III. Specification Principles

**规范原则**：命名清晰、结构统一、字段完整、格式严格符合 OpenAPI 3.0。

**具体要求**：
- 命名必须清晰易懂，避免缩写和歧义（英文命名采用 camelCase 或 snake_case，中文注释使用标准术语）
- 结构必须统一，遵循项目模板定义的章节格式
- API 接口字段必须完整，包含类型、是否必填、默认值、描述
- 所有 API 规范必须符合 OpenAPI 3.0 标准（YAML/JSON 格式）
- 数据模型（data-model.md）必须与 API 契约（contracts/）保持一致

**Rationale**: 确保接口文档的标准化和可读性，便于前端集成和自动化代码生成。

### IV. Collaboration Principles

**协作原则**：AI 生成必须人工审核，所有修改必须先验证再提交。

**具体要求**：
- `/speckit.specify`、`/speckit.plan`、`/speckit.tasks` 等命令生成的文档必须经过人工审核才能进入下一阶段
- AI 实现代码前，必须运行验证脚本（如测试、lint、格式检查）
- 所有代码提交（commit）前必须验证：
  - 代码格式符合规范（如 black、ruff）
  - 测试通过（如果包含测试）
  - 构建成功
- 严禁直接 push 到 main 分支

**Rationale**: 人工审核保证质量和安全性，验证机制减少错误和回滚。

### V. AI Behavior Principles

**AI 行为原则**：只输出与项目相关内容，不编造信息，格式严格遵循章程，不随意扩展。

**具体要求**：
- AI 只输出与当前功能相关的代码、文档和配置
- 不编造项目中不存在的接口、配置或模块
- 严格遵循章程和模板定义的格式，不自行扩展章节或字段
- 遇到章程未覆盖的场景，必须使用 `[NEEDS CLARIFICATION]` 标记并等待人工决策
- 不假设或猜测技术选型，必须在 plan.md 中明确声明

**Rationale**: 确保 AI 输出的可预测性和准确性，避免引入未知变量。

### VI. Delivery Principles

**交付原则**：输出结构清晰、可直接运行、可直接集成。

**具体要求**：
- 所有生成代码必须包含清晰的目录结构和模块划分
- 代码必须可直接运行（无需额外配置或手动修复）
- 生成的接口规范可直接用于前端集成（如 Swagger UI 可直接访问）
- 配置文件必须包含所有必需参数，并提供默认值
- 交付内容必须包含：
  - 可运行的源代码
  - 完整的依赖声明（requirements.txt / pyproject.toml）
  - 环境配置示例（.env.example）
  - 快速开始指南（quickstart.md）

**Rationale**: 降低集成成本，确保交付物立即可用。

## Technical Standards

### Language & Runtime

- **Python 版本**: 3.12（必须）
- **包管理**: pip / conda
- **环境隔离**: Conda 环境（必须）
- **虚拟环境**: `.venv` 或 conda env
- **Python 风格**: PEP 8（使用 black/ruff 格式化）

### API Specification

- **规范标准**: OpenAPI 3.0（必须）
- **输出格式**: YAML（优先）或 JSON
- **文件位置**: `specs/###-feature/contracts/`
- **命名规范**: RESTful 资源命名（小写，使用连字符）
- **字段要求**:
  - 必须包含 `description`
  - 类型必须明确（string, integer, boolean, array, object）
  - 数组项和对象属性必须定义子结构
  - 必需字段必须标记 `required: true`

### Code Organization

- **源码目录**: `src/`（单项目）或 `backend/src/`（Web 应用）
- **模块结构**: `models/`, `services/`, `api/`（REST）或 `cli/`（命令行）
- **测试目录**: `tests/`（包含 contract/, integration/, unit/ 子目录）
- **配置目录**: `config/` 或项目根目录（如 .env 文件）

## Collaboration Workflow

### Development Phases

1. **Constitution**（可选，首次运行）: 定义项目原则和技术标准
2. **Specify**: 创建功能规范（spec.md），AI 生成后必须人工审核
3. **Clarify**（可选）: 澄清规范中的未明确需求
4. **Plan**: 创建技术方案（plan.md），包含技术栈、架构和数据模型
5. **Tasks**: 生成任务列表（tasks.md），按用户故事组织
6. **Checklist**（可选）: 生成质量检查清单，验证规范和方案的一致性
7. **Analyze**（可选）: 分析规范、方案、任务的一致性
8. **Implement**: 执行实现，必须先验证再提交
9. **TasksToIssues**（可选）: 将任务转换为 GitHub Issues

### Validation Requirements

**代码提交前必须验证**：

| 检查项 | 命令 | 通过条件 |
|---------|--------|---------|
| 代码格式 | `black .` 或 `ruff format .` | 无格式错误 |
| Linting | `ruff check .` 或 `flake8` | 无 lint 错误 |
| 类型检查 | `mypy src/`（可选） | 无类型错误 |
| 测试 | `pytest` | 所有测试通过 |
| 构建 | `python -m build` 或 `python setup.py sdist` | 构建成功 |

### Review Process

- **Spec 审核**: 规范（spec.md）生成后，必须由产品负责人或技术负责人审核
- **Plan 审核**: 方案（plan.md）完成后，必须由架构师或技术负责人审核
- **Code Review**: 代码实现后，必须经过同行评审（Pull Request）
- **验证要求**:
  - 功能需求与规范一致
  - 接口符合 OpenAPI 3.0 标准
  - 代码遵循项目结构
  - 测试覆盖核心逻辑

### Git Commit Standards

- **格式**: `<type>: <subject>`（例：`feat: 添加用户登录接口`）
- **Type**: feat, fix, docs, style, refactor, test, chore, perf, ci
- **每个 Spec 步骤完成后至少提交一次 commit**
- AI 生成需添加：`Co-Authored-By: Claude <noreply@anthropic.com>`
- 提交前必须通过验证检查

## Governance

### Amendment Procedure

- **章程修订**: 必须通过 `/speckit.constitution` 命令进行
- **版本控制**: 语义化版本（MAJOR.MINOR.PATCH）
  - MAJOR: 原则删除或重大变更，影响向后兼容性
  - MINOR: 新增原则或扩展，向后兼容
  - PATCH: 澄清、措辞调整，无语义变更
- **生效日期**: 修订后立即生效，记录在 `Last Amended` 字段

### Compliance Review

- **所有 PR/代码评审**必须验证是否符合章程原则
- **Constitution Check**: plan.md 中的 Constitution Check 部分必须检查所有原则合规性
- **违规处理**:
  - CRITICAL（违反 MUST 原则）: 必须修正后才能继续
  - 复杂性未经充分论证不得引入
  - 技术选型偏离章程必须记录理由并获得批准

### Guidance Reference

- **运行时开发指导**: 参考 `.specify/memory/constitution.md`（本文件）
- **命令执行指南**: 参考 `.claude/commands/` 目录下的命令文件
- **模板参考**: 所有文档模板位于 `.specify/templates/` 目录

**Version**: 1.1.0 | **Ratified**: 2025-02-12 | **Last Amended**: 2025-02-13
