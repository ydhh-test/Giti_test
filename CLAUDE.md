# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个**规范驱动开发（Spec-Driven Development）框架**，用于内部测试 VibeCoding 协作方法。此项目不是最终交付代码仓库。业务内容为 JT 轮胎后处理部分，详细信息在飞书文档中。

**重要约定**：请不要直接 push 到 main 分支。

## SpecKit 工作流

该仓库实现了一个结构化的开发工作流，使用 Claude 斜杠命令。工作流遵循以下顺序：

```
Constitution (章程) → Specify (规范) → Plan (方案) → Tasks (任务) → Implement (实现)
```

### 可用的斜杠命令

按以下顺序执行命令来开发新功能：

1. `/speckit.constitution` - 定义或更新项目原则和约束
2. `/speckit.specify` - 从自然语言描述创建功能规范
3. `/speckit.clarify` - 对未明确的需求提出澄清问题（可选）
4. `/speckit.plan` - 创建技术实现方案
5. `/speckit.tasks` - 生成可执行的任务列表
6. `/speckit.checklist` - 生成质量检查清单
7. `/speckit.analyze` - 分析跨文档的一致性
8. `/speckit.implement` - 执行实现计划
9. `/speckit.taskstoissues` - 将任务转换为 GitHub Issues（可选）

### 分支命名规范

所有功能分支必须遵循格式：`###-short-name`（例如 `001-user-auth`、`002-api-integration`）

`create-new-feature.sh` 脚本会自动：
- 从功能描述生成分支名称
- 分配下一个可用编号（检查本地和远程分支）
- 过滤掉停用词（a、an、the、to、for、of 等）
- 限制分支名称不超过 GitHub 的 244 字节限制

使用示例：
```bash
.specify/scripts/bash/create-new-feature.sh --json "Add user authentication"
# 输出: {"BRANCH_NAME":"001-user-auth","SPEC_FILE":".../001-user-auth/spec.md","FEATURE_NUM":"001"}
```

### 脚本使用

`.specify/scripts/bash/` 中的关键自动化脚本：

**create-new-feature.sh**：创建新功能分支和规范目录
```bash
.specify/scripts/bash/create-new-feature.sh [--json] [--short-name <name>] [--number N] <feature_description>
```

**setup-plan.sh**：初始化方案目录结构
```bash
.specify/scripts/bash/setup-plan.sh [--json]
```

**check-prerequisites.sh**：验证所需文件存在
```bash
.specify/scripts/bash/check-prerequisites.sh [--json] [--require-tasks] [--include-tasks]
```

所有脚本支持 `--json` 标志以输出机器可读格式，并支持非 git 仓库的回退机制。

### 目录结构

```
.specify/
├── memory/constitution.md          # 项目章程（原则、约束）
├── templates/                       # 所有文档的模板
│   ├── spec-template.md            # 功能规范
│   ├── plan-template.md            # 技术方案
│   ├── tasks-template.md           # 任务列表
│   └── ...
└── scripts/bash/                   # 自动化脚本
    ├── common.sh                   # 共享函数（get_repo_root、get_feature_paths）
    ├── create-new-feature.sh
    ├── setup-plan.sh
    └── check-prerequisites.sh

specs/
└── ###-feature-name/               # 每个功能有独立目录
    ├── spec.md                     # 功能规范
    ├── plan.md                     # 技术方案
    ├── research.md                 # 研究发现
    ├── data-model.md               # 数据模型设计
    ├── tasks.md                    # 任务列表
    ├── quickstart.md               # 快速开始指南
    ├── contracts/                  # API 契约
    └── checklists/                 # 质量检查清单
```

### 开发工作流

1. **从章程开始** - 运行 `/speckit.constitution` 先定义项目原则
2. **创建规范** - 使用 `/speckit.specify <功能描述>` 生成初始规范
3. **需要时澄清** - 如果规范有 `[NEEDS CLARIFICATION]` 标记，运行 `/speckit.clarify`
4. **创建方案** - 执行 `/speckit.plan` 设计技术方案
5. **生成任务** - 运行 `/speckit.tasks` 创建实现任务列表
6. **可选验证** - 使用 `/speckit.checklist` 进行质量检查，`/speckit.analyze` 进行一致性分析
7. **实现** - 执行 `/speckit.implement` 实现任务
8. **跟踪 Issues** - 如需要，使用 `/speckit.taskstoissues` 导出到 GitHub

### 核心设计原则

- **用户故事优先级**：每个用户故事（US1、US2、US3...）都有优先级（P1、P2、P3...），应可独立测试和部署
- **MVP 优先**：P1 用户故事构成 MVP；在添加 P2+ 之前先完成并验证它们
- **独立可测试性**：每个用户故事必须可独立实现和测试
- **规范驱动**：规范必须避免实现细节；关注 WHAT 和 WHY，而不是 HOW
- **技术无关**：成功标准必须可衡量且不引用特定技术

### 模板系统

所有文档工件都从模板生成：
- `spec-template.md`：用户故事、功能需求、成功标准
- `plan-template.md`：技术上下文、架构、项目结构
- `tasks-template.md`：按用户故事组织的基于阶段的任务
- `checklist-template.md`：质量验证检查清单

模板包含 `NEEDS CLARIFICATION` 标记，用于需要用户输入的方面。

### 路径解析

`common.sh` 脚本提供了查找路径的工具：
- `get_repo_root()`：查找仓库根目录（支持 git 和非 git 仓库）
- `get_current_branch()`：获取当前分支（读取 SPECIFY_FEATURE 环境变量或 git）
- `get_feature_paths()`：返回所有功能相关的路径作为 shell 变量
- `find_feature_dir_by_prefix()`：通过数字前缀查找规范目录（支持一个规范对应多个分支）

在脚本中使用 `eval $(get_feature_paths)` 加载所有路径变量。

### 章程合规性

在功能规划之前，检查 `.specify/memory/constitution.md`：
- 核心原则（例如"测试优先"、"库优先"）
- 技术约束（必需的框架、语言）
- 质量标准（测试要求、文档）
- 治理规则（什么优先于什么、修订流程）

章程当前处于模板状态，需要填写实际项目需求。

### 规范质量门控

当 `/speckit.specify` 完成时，它创建 `specs/###-feature/checklists/requirements.md`，包含验证标准：

- 规范中没有实现细节
- 所有需求可测试且无歧义
- 成功标准可衡量且与技术无关
- 最多允许 3 个 `[NEEDS CLARIFICATION]` 标记
- 所有必需部分已完成

规范在所有关键检查清单项通过之前不能进入规划阶段。

### 任务组织

`tasks.md` 中的任务遵循以下结构：
- **阶段 1**：设置（共享基础设施）
- **阶段 2**：基础（所有用户故事的阻塞前提条件）
- **阶段 3+**：用户故事（按优先级 P1、P2、P3... 组织）
- **最终阶段**：完善和横切关注点

任务标记：
- `[P]` - 可并行运行（不同文件，无依赖）
- `[US#]` - 属于哪个用户故事

关键检查点：在阶段 2（基础）完成之前，不能开始任何用户故事工作。

### Git 集成

- 脚本支持 git 和非 git 仓库
- 分支验证检查 `###-` 前缀模式
- 检查可用编号时会获取远程分支
- 该框架优雅地处理 `--no-git` 初始化

### 测试理念

测试默认为**可选**，仅在功能规范中明确要求时才包含。如果包含测试：
- 先编写测试（红-绿-重构循环）
- 确保测试在实现之前失败
- 按用户故事组织测试以进行独立验证
