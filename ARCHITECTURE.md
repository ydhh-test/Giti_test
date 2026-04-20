# ARCHITECTURE

## 1. Purpose

本文档定义项目的分层架构、目录职责、依赖方向和扩展约束。  
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
- `src.utils.image_utils`
- `src.json_utils`
- `src.models`

## 5. Layer Model

系统采用以下分层模型：

```text
┌────────────────────────────────────────────────────────┐
│         接入层 (src.api)                                │
│  pipeline_1 | pipeline_2 | ...                         │
├────────────────────────────────────────────────────────┤
│         节点层 (src.nodes)                          │
│  evaluate_single_small_image | ...                     │
├────────────────────────────────────────────────────────┤
│         规则层 (src.rules)                              │
│  features.rule_x | scores.rule_x  |...                 │
│  (计算图像特征)    | (计算特征得分)   |...                 │
├────────────────────────────────────────────────────────┤
│         算法层 (src.core)                               │
│  海路比算法 | 连续性算法 | 横沟检测算法｜...                 │
├────────────────────────────────────────────────────────┤
│         公共函数...                                      │
│  src.utils.image_utils | src.json_utils  | src.models   │
│  (图像工具函数)          | (json工具函数)   |  (数据类)     │
└────────────────────────────────────────────────────────┘
```

对应目录如下：

- `src.api` -> 接入层
- `src.nodes` -> 节点层
- `src.rules` -> 规则层
- `src.core` -> 算法层
- `src.utils.image_utils` / `src.json_utils` / `src.models` -> 公共支撑层

## 6. Directory Responsibilities

### 6.1 `src.api`

**定位**：对外接入层。

**MUST**：

- 接收外部输入
- 选择并启动具体 pipeline
- 返回统一格式的处理结果

**SHOULD**：

- 保持接口薄层化
- 不在该层堆积复杂分析逻辑

**MUST NOT**：

- 直接实现底层图像算法
- 直接承载复杂评分规则

---

### 6.2 `src.nodes`

**定位**：流程节点层。

**MUST**：

- 定义和组织处理节点
- 编排节点执行顺序
- 管理节点输入输出
- 调用规则层完成分析

**SHOULD**：

- 保持节点可复用
- 让节点层专注于流程组织

**MUST NOT**：

- 在节点层实现底层算法
- 在节点层堆积大量业务评分细节

---

### 6.3 `src.rules`

**定位**：规则层。

**MUST**：

- 定义特征提取规则
- 定义评分或判定规则
- 调用算法层能力并组织结果

**SHOULD**：

- 将业务解释逻辑放在规则层
- 将特征规则与评分规则分开组织

**MUST NOT**：

- 将纯底层图像处理逻辑留在规则层
- 依赖具体 API 入口实现

**当前已知规则类型**：

- `features.rule_x`
- `scores.rule_x`

---

### 6.4 `src.core`

**定位**：核心算法层。

**MUST**：

- 实现底层图像分析算法
- 向规则层提供稳定、可复用的算法能力

**SHOULD**：

- 保持与业务规则解耦
- 聚焦算法本身的输入、计算和输出

**MUST NOT**：

- 依赖 `src.rules`
- 依赖 `src.api`
- 直接承载业务评分逻辑

**当前已知算法示例**：

- 海路比算法
- 连续性算法
- 横沟检测算法

---

### 6.5 `src.utils.image_utils`

**定位**：图像处理通用工具。

**MUST**：

- 提供通用图像处理函数

**MUST NOT**：

- 承载业务规则
- 承载 pipeline 编排逻辑

---

### 6.6 `src.json_utils`

**定位**：JSON 工具模块。

**MUST**：

- 提供 JSON 读写、转换或序列化相关能力

**MUST NOT**：

- 承载业务分析逻辑

---

### 6.7 `src.models`

**定位**：共享数据模型层。

**MUST**：

- 定义跨层共享的数据结构
- 约束输入、特征、评分和输出对象的表达方式

**SHOULD**：

- 保持模型命名统一
- 减少无约束字典在层间传递

**MUST NOT**：

- 混入具体 pipeline 逻辑
- 混入算法实现

## 7. Dependency Rules

允许的主依赖方向如下：

- `src.api` -> `src.nodes`
- `src.nodes` -> `src.rules`
- `src.rules` -> `src.core`
- `src.core` -> `src.utils.image_utils`
- `src.core` -> `src.models`
- `src.rules` -> `src.models`
- `src.nodes` -> `src.models`
- `src.api` -> `src.models`

共享模块可被上层依赖：

- `src.utils.image_utils`
- `src.json_utils`
- `src.models`

禁止的依赖方向如下：

- `src.core` -> `src.rules`
- `src.core` -> `src.nodes`
- `src.core` -> `src.api`
- `src.rules` -> `src.api`
- `src.utils.image_utils` -> `src.rules`
- `src.utils.image_utils` -> `src.nodes`
- `src.utils.image_utils` -> `src.api`
- `src.models` -> `src.rules`
- `src.models` -> `src.nodes`
- `src.models` -> `src.api`

## 8. Execution Contract

典型执行顺序应为：

1. 请求进入 `src.api`
2. `src.api` 选择 pipeline
3. pipeline 调用 `src.nodes`
4. `src.nodes` 调用 `src.rules`
5. `src.rules` 调用 `src.core`
6. 各层按需使用共享工具与模型
7. 结果逐层返回至 `src.api`

## 9. Extension Rules

新增功能时应遵循以下规则：

### 9.1 新增外部入口

**应放在**：

- `src.api`

**不应放在**：

- `src.rules`
- `src.core`

---

### 9.2 新增流程节点

**应放在**：

- `src.nodes`

**适用场景**：

- 新增流程步骤
- 重组已有规则执行顺序
- 抽取可复用流程片段

---

### 9.3 新增业务规则

**应放在**：

- `src.rules`

**适用场景**：

- 新增特征规则
- 新增评分规则
- 调整业务判定逻辑

---

### 9.4 新增算法能力

**应放在**：

- `src.core`

**适用场景**：

- 新增底层图像分析算法
- 优化已有算法实现
- 提供新的可复用计算能力

---

### 9.5 新增通用能力

**应放在**：

- `src.utils.image_utils`
- `src.json_utils`
- `src.models`

**前提**：

- 该能力必须是跨模块复用的通用能力
- 不得将业务规则伪装成工具函数

## 10. Architecture Constraints

以下约束默认长期生效：

- 接入层负责入口，不负责底层计算
- 节点层负责编排，不负责底层算法实现
- 规则层负责业务解释，不负责替代算法层
- 算法层负责计算，不负责业务评分策略
- 公共支撑层负责通用能力，不负责业务决策
- 数据模型应集中定义，不应在各层随意漂移

## 11. Known Gaps

当前文档仍缺少以下可执行细节，后续应补充：

- 各目录下的真实文件清单
- 真实 pipeline 列表
- 典型 pipeline 的输入输出定义
- 特征对象、评分对象、结果对象的正式模型定义
- `src.rules` 与 `src.core` 的边界判定示例
- 配置管理规则
- 错误处理规则
- 测试分层策略

## 12. Review Checklist

提交代码时，建议至少检查以下问题：

- 新代码是否放在正确目录
- 是否出现跨层反向依赖
- 是否将业务规则错误地下沉到工具层
- 是否将底层算法错误地写进规则层或节点层
- 是否新增了未经统一定义的数据结构
- 是否破坏了 `src.api -> src.nodes -> src.rules -> src.core` 的主链路

## 13. Status

当前文档状态：**Draft**

说明：

- 已定义高层分层结构与约束
- 已补充系统概述、核心技术栈和整体架构图
- 尚未补齐真实模块、数据模型和示例流程
- 在补齐缺失信息前，本文件应作为“架构方向约束”使用，而非“完整实现说明”
