# ARCHITECTURE

## 1. Purpose

本文档定义项目的分层架构、代码目录职责、依赖方向和扩展约束。  
新增模块、重构代码或检查架构一致性时，应以本文档为基准。

## 2. System Overview

轮胎 AI 模式识别系统采用模块化分层架构，实现从图像输入到质量评分的端到端自动化流程。

系统通过将接入、流程编排、规则计算、底层算法和公共支撑能力进行分层，降低模块耦合，提升可维护性、可扩展性和复用性。

## 3. Tech Stack

核心技术栈如下：

- 编程语言：Python 3.12
- 图像处理：OpenCV、Pillow
- 数据处理：NumPy
- 测试框架：Pytest
- 日志系统：Python logging

## 4. Scope

本文档覆盖以下目录与分层关系：

- `src.api`
- `src.nodes`
- `src.rules`
- `src.core`
- `src.utils`
- `src.models`
- `src.config`

## 5. Layer Model

系统采用以下分层模型：

```text
┌────────────────────────────────────────────────────────┐
│ 接入层 (src.api)                                       │
│ generation.py | stitching.py | scoring.py | splitting.py │
├────────────────────────────────────────────────────────┤
│ 节点层 (src.nodes)                                     │
│ small_image_evaluator.py | stitch_scheme_generator.py │
│ big_image_stitcher.py | big_image_evaluator.py        │
│ geometry_scorer.py | big_image_splitter.py            │
├────────────────────────────────────────────────────────┤
│ 规则层 (src.rules)                                     │
│ features.rule_x | scores.rule_x | ...                 │
├────────────────────────────────────────────────────────┤
│ 算法层 (src.core)                                      │
│ detection/* | stitching/*                             │
├────────────────────────────────────────────────────────┤
│ 公共支撑层                                             │
│ src.utils | src.models | src.config                   │
└────────────────────────────────────────────────────────┘
```

对应目录如下：

- `src.api` -> 接入层
- `src.nodes` -> 节点层
- `src.rules` -> 规则层
- `src.core` -> 算法层
- `src.utils` / `src.models` / `src.config` -> 公共支撑层

## 6. Code Layout

当前代码架构目录如下：

```text
tire-ai-pattern/
├── src/                               # 项目主源码根目录，所有业务代码入口
│   ├── __init__.py
│   ├── api/                           # 对外接口层，封装标准 pipeline
│   │   ├── __init__.py
│   │   ├── generation.py              # pipeline-1：小图生成大图、血缘、特征与评分
│   │   ├── stitching.py               # pipeline-2：基于血缘重拼大图（深度编辑）
│   │   ├── scoring.py                 # pipeline-3：使用新的规则参数，更新总评分
│   │   └── splitting.py               # pipeline-4：大图按规则拆分为小图
│   │
│   ├── core/                          # 核心算法层，底层检测与拼接算法（原则上一个算法一个文件）
│   │   ├── __init__.py
│   │   ├── detection/                 # 检测算法
│   │   │   ├── __init__.py
│   │   │   ├── pattern_continuity.py # 纹理连续性检测算法
│   │   │   └── groove_intersection.py# 横沟相交/干扰检测算法
│   │   └── stitching/                 # 拼接算法
│   │       ├── __init__.py
│   │       ├── horizontal_stitch.py  # 水平方向大图拼接算法
│   │       └── vertical_stitch.py    # 垂直方向大图拼接算法
│   │
│   ├── nodes/                         # 流程节点层，pipeline 拓扑中的可复用执行单元
│   │   ├── __init__.py
│   │   ├── small_image_evaluator.py  # 节点-1：小图评估
│   │   ├── stitch_scheme_generator.py# 节点-2：拼接方案生成
│   │   ├── big_image_stitcher.py     # 节点-3：拼接大图
│   │   ├── big_image_evaluator.py    # 节点-4：大图评估
│   │   ├── geometry_scorer.py        # 节点-5：几何合理性业务评分
│   │   └── big_image_splitter.py     # 节点-6：大图拆分
│   │
│   ├── rules/                         # 业务规则层，包含特征规则与评分规则
│   │   ├── __init__.py
│   │   ├── features/                  # 特征计算规则，按编号 rule_1 ~ rule_n 组织
│   │   │   ├── __init__.py
│   │   │   ├── rule_1.py              # 特征规则 1：指定业务维度特征计算
│   │   │   ├── rule_2.py              # 特征规则 2：指定业务维度特征计算
│   │   │   └── rule_n.py              # 特征规则 N：指定业务维度特征计算
│   │   └── scores/                    # 评分规则，按编号 rule_1 ~ rule_n 组织
│   │       ├── __init__.py
│   │       ├── rule_1.py              # 评分规则 1：指定业务维度打分逻辑
│   │       ├── rule_2.py              # 评分规则 2：指定业务维度打分逻辑
│   │       └── rule_n.py              # 评分规则 N：指定业务维度打分逻辑
│   │
│   ├── models/                        # 数据模型层，定义业务数据类
│   │   ├── __init__.py
│   │   ├── tire_struct.py             # TireStruct：业务总数据结构
│   │   ├── small_image.py             # SmallImage：小图数据结构与元信息
│   │   ├── big_image.py               # BigImage：大图、血缘、结果与评分数据结构
│   │   └── rules_config.py            # RulesConfig：规则与评分配置数据结构
│   │
│   ├── utils/                         # 通用工具层，与具体业务规则无关
│   │   ├── __init__.py
│   │   ├── image_utils.py             # 图像 base64 / ndarray 转换、裁剪与绘制工具
│   │   ├── json_utils.py              # JSON 序列化、字典处理与文件读写工具
│   │   └── logger.py                  # 统一日志配置、输出格式与文件记录
│   │
│   └── config/                        # 配置模块，仅定义默认 rules_config
│       ├── __init__.py
│       └── default_rules_config.py    # 默认 rules_config 定义
│
├── tests/                             # 测试代码根目录，验证算法、节点与接口正确性
│   ├── datasets/                      # 测试专用图片、配置与样例数据
│   ├── unittests/                     # 单元测试，结构与 src 镜像对应
│   └── integrations/                  # 集成测试，覆盖跨层流程与接口联调
│
├── docs/                              # 项目文档根目录
│   ├── plans/                         # 实施计划、任务拆解与 Claude Plan 输出归档
│   └── checklist/                     # 代码检查清单、架构约束与审查规则
│
├── scripts/                           # 运维、数据处理、批量运行与部署脚本
├── .logs/                             # debug 模式下的运行日志输出目录（加入 .gitignore）
├── .results/                          # debug 模式下的中间结果图与结果 JSON 输出目录（加入 .gitignore）
├── ARCHITECTURE.md                    # 项目架构设计文档
├── CONTRIBUTING.md                    # 代码提交、开发与协作规范
├── README.md                          # 项目说明、快速开始与使用示例
└── requirements.txt                   # Python 依赖列表
```

## 7. Directory Responsibilities

### 7.1 `src.api`

**定位**：对外接口层，封装标准 pipeline。

**MUST**：

- 对外暴露标准 pipeline 入口
- 根据业务场景组合 `src.nodes` 中的节点拓扑
- 管理 pipeline 的输入输出协议
- 组织 generation、stitching、scoring、splitting 等业务入口

**SHOULD**：

- 保持入口薄层化
- 将执行逻辑下沉到 `src.nodes`
- 将规则实现下沉到 `src.rules`

**MUST NOT**：

- 直接实现底层图像算法
- 直接承载单条特征规则或评分规则
- 在 API 层堆积节点内部执行细节

**当前已知模块示例**：

- `generation.py`
- `stitching.py`
- `scoring.py`
- `splitting.py`

---

### 7.2 `src.nodes`

**定位**：流程节点层，pipeline 拓扑中的可复用执行单元。

**MUST**：

- 提供可被多个 pipeline 复用的执行节点
- 承担小图评估、拼接方案生成、拼接大图、大图评估、几何合理性业务评分、大图拆分等节点能力
- 接收上层 pipeline 调度，组织规则与算法调用
- 输出结构化中间结果，供后续节点或 pipeline 使用

**SHOULD**：

- 保持节点职责单一、边界清晰
- 让节点成为 pipeline 编排中的稳定拓扑单元
- 将规则判断下沉到 `src.rules`
- 将底层算法调用收敛到受控路径

**MUST NOT**：

- 在节点层定义对外 API 协议
- 在节点层直接实现底层算法
- 在节点层堆积大量单条规则实现细节

**当前已知模块示例**：

- `small_image_evaluator.py`
- `stitch_scheme_generator.py`
- `big_image_stitcher.py`
- `big_image_evaluator.py`
- `geometry_scorer.py`
- `big_image_splitter.py`

---

### 7.3 `src.rules`

**定位**：规则层。

**MUST**：

- 定义特征提取规则
- 定义评分或判定规则
- 调用算法层能力并组织结果

**SHOULD**：

- 将业务解释逻辑放在规则层
- 将特征规则与评分规则分开组织
- 按业务规则编号组织规则文件

**MUST NOT**：

- 将纯底层图像处理逻辑留在规则层
- 依赖具体 API 入口实现

**当前已知规则类型**：

- `features.rule_x`
- `scores.rule_x`

**说明**：

- 规则文件按业务规则编号组织，规则编号是规则管理的主索引。

---

### 7.4 `src.core`

**定位**：核心算法层。

**MUST**：

- 实现底层图像分析算法
- 向规则层提供稳定、可复用的算法能力

**SHOULD**：

- 保持与业务规则解耦
- 聚焦算法本身的输入、计算和输出
- 按算法域组织子模块，例如检测算法与拼接算法

**MUST NOT**：

- 依赖 `src.rules`
- 依赖 `src.api`
- 直接承载业务评分逻辑

**当前已知模块示例**：

- `detection/pattern_continuity.py`
- `detection/groove_intersection.py`
- `stitching/horizontal_stitch.py`
- `stitching/vertical_stitch.py`

---

### 7.5 `src.utils`

**定位**：通用工具层，与具体业务规则无关。

**MUST**：

- 提供跨模块复用的通用工具函数
- 为图像处理、JSON 处理、日志输出等提供基础支持

**SHOULD**：

- 保持工具函数通用、独立、可复用
- 避免与具体业务规则强耦合

**MUST NOT**：

- 承载业务规则
- 承载 pipeline 或节点编排逻辑

**当前已知模块示例**：

- `image_utils.py`
- `json_utils.py`
- `logger.py`

---

### 7.6 `src.models`

**定位**：数据模型层，定义业务数据类。

**MUST**：

- 定义业务主数据结构与跨层共享对象
- 承载 `TireStruct`、`SmallImage`、`BigImage`、`RulesConfig` 等核心数据模型
- 统一表达图像输入、拼接结果、血缘关系、评分结果与规则配置

**SHOULD**：

- 保持模型命名统一
- 通过嵌套数据类组织复杂业务对象
- 减少无约束字典在层间传递

**MUST NOT**：

- 混入具体流程逻辑
- 混入算法实现

**当前已知模块示例**：

- `tire_struct.py`
- `small_image.py`
- `big_image.py`
- `rules_config.py`

---

### 7.7 `src.config`

**定位**：配置模块。

**MUST**：

- 定义默认 `rules_config`
- 提供默认规则参数和默认评分参数

**SHOULD**：

- 保持配置声明集中、稳定、可追踪
- 让配置只表达默认值和启用方式，不表达规则实现细节

**MUST NOT**：

- 承载规则实现
- 承载算法实现
- 承载 pipeline 编排逻辑

**当前已知模块示例**：

- `default_rules_config.py`

## 8. Dependency Rules

允许的主依赖方向如下：

- `src.api` -> `src.nodes`
- `src.nodes` -> `src.rules`
- `src.rules` -> `src.core`
- `src.api` -> `src.utils`
- `src.api` -> `src.models`
- `src.api` -> `src.config`
- `src.nodes` -> `src.utils`
- `src.nodes` -> `src.models`
- `src.nodes` -> `src.config`
- `src.rules` -> `src.utils`
- `src.rules` -> `src.models`
- `src.rules` -> `src.config`
- `src.core` -> `src.utils`
- `src.core` -> `src.models`

共享模块可被上层依赖：

- `src.utils`
- `src.models`
- `src.config`

禁止的依赖方向如下：

- `src.core` -> `src.rules`
- `src.core` -> `src.nodes`
- `src.core` -> `src.api`
- `src.rules` -> `src.api`
- `src.rules` -> `src.nodes`
- `src.utils` -> `src.core`
- `src.utils` -> `src.rules`
- `src.utils` -> `src.nodes`
- `src.utils` -> `src.api`
- `src.models` -> `src.core`
- `src.models` -> `src.rules`
- `src.models` -> `src.nodes`
- `src.models` -> `src.api`
- `src.config` -> `src.core`
- `src.config` -> `src.rules`
- `src.config` -> `src.nodes`
- `src.config` -> `src.api`

## 9. Execution Contract

典型执行顺序应为：

1. 请求进入 `src.api`
2. API 层选择 `generation`、`stitching`、`scoring` 或 `splitting` pipeline
3. pipeline 按业务拓扑调用 `src.nodes` 中的执行节点
4. 节点调用 `src.rules` 中的特征规则或评分规则
5. 规则调用 `src.core` 中的底层算法
6. 各层通过 `src.models` 传递结构化数据，并按需使用 `src.utils`
7. `src.config` 提供默认 `rules_config` 和默认评分参数
8. 最终结果由 API 层统一输出

## 10. Extension Rules

新增功能时应遵循以下规则：

### 10.1 新增外部入口

**应放在**：

- `src.api`

**适用场景**：

- 新增 generation 类 pipeline
- 新增 stitching 类 pipeline
- 新增 scoring 类 pipeline
- 新增 splitting 类 pipeline
- 新增新的对外处理流程

**不应放在**：

- `src.rules`
- `src.core`

---

### 10.2 新增流程节点

**应放在**：

- `src.nodes`

**适用场景**：

- 新增小图评估节点
- 新增拼接方案生成节点
- 新增拼接大图节点
- 新增大图评估节点
- 新增几何合理性评分节点
- 新增大图拆分节点
- 抽取可复用的 pipeline 执行单元

---

### 10.3 新增业务规则

**应放在**：

- `src.rules`

**适用场景**：

- 新增特征规则
- 新增评分规则
- 调整业务判定逻辑
- 按新增业务规则编号扩展规则实现

---

### 10.4 新增算法能力

**应放在**：

- `src.core`

**适用场景**：

- 新增底层图像分析算法
- 优化已有算法实现
- 提供新的可复用计算能力

---

### 10.5 新增通用能力

**应放在**：

- `src.utils`
- `src.models`
- `src.config`

**前提**：

- 该能力必须是跨模块复用的通用能力
- 不得将业务规则伪装成工具函数
- 不得将规则实现写入配置模块

## 11. Architecture Constraints

以下约束默认长期生效：

- 接入层负责入口，不负责底层计算
- 节点层负责编排与执行单元复用，不负责底层算法实现
- 规则层负责业务解释，不负责替代算法层
- 算法层负责计算，不负责业务评分策略
- 工具层负责通用支持，不负责业务决策
- 数据模型应集中定义，不应在各层随意漂移
- 配置层只定义默认规则配置与默认参数，不承载规则实现

## 12. Known Gaps

当前文档仍缺少以下可执行细节，后续应补充：

- generation、stitching、scoring、splitting 各 pipeline 的完整输入输出定义
- `src.nodes` 中各执行节点的接口契约与节点拓扑关系
- `TireStruct`、`SmallImage`、`BigImage`、`RulesConfig` 的正式字段定义
- `a.json`、`b.json`、`c.json` 的结构约束与更新时机
- `src.rules` 与 `src.core` 的边界判定示例
- debug 模式下 `.logs` 与 `.results` 的创建与清理规则
- 配置加载与默认 `rules_config` 的覆盖机制
- 测试分层策略与数据样例约束

## 13. Review Checklist

提交代码时，建议至少检查以下问题：

- 新代码是否放在正确目录
- 是否出现跨层反向依赖
- 是否在 `src.api` 中堆积节点内部执行细节
- 是否在 `src.nodes` 中堆积单条规则实现
- 是否将底层算法错误地写进 `src.rules` 或 `src.nodes`
- 是否将规则实现错误写入 `src.config`
- 是否新增了未经统一定义的数据结构
- 是否破坏了 `src.api -> src.nodes -> src.rules -> src.core` 的主链路

## 14. Status

当前文档状态：**Draft**

说明：

- 已定义高层分层结构与约束
- 已补充当前代码目录结构
- 已补充 API、节点、规则、算法、模型、配置层职责
- 尚未补齐字段级数据模型、节点拓扑和接口契约
- 在补齐缺失信息前，本文件应作为“架构方向约束”与“目录边界规范”使用，而非完整实现说明
