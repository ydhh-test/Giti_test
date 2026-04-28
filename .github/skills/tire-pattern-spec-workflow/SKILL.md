---
name: tire-pattern-spec-workflow
description: "**WORKFLOW SKILL** — 把 GITI 轮胎花纹规格表（主沟/横沟/横向钢片/纵向钢片&细沟/连续性/海陆比）落地到本项目 rules、algorithms、configs、tests。USE WHEN: 新增或更新轮胎花纹规格相关规则（rule1-19）；按规格表/图纸生成 rule 实现计划（plans/rules/*.md）；校验生成图片是否符合量化指标（海陆比 28-35%、钢片&横沟连续性 60-70%、主沟 3-4 条等）；解读 POC 阶段参数（主沟10mm、横沟R1/5 3.5mm 其余1.8mm、横向钢片0.6mm、纵向钢片&细沟1mm）；把 RIB1-5 per-rib 数量/宽度约束翻译成 configs/*.py 的 dataclass；把规格项映射到 rules/ 和 algorithms/detection 或 scoring。DO NOT USE FOR: 纯图像预处理（preprocessor）、推理服务（inference）、与花纹量化无关的工程任务。INVOKES: read_file/grep_search 检索现有 rule 与 config、create_file 生成 plan 与代码、tests 运行器校验量化指标。"
---

# GITI 轮胎花纹规格落地工作流

把规格图（RIB1-5，总长210mm节距，TDW 170mm，PDW 220mm）中定义的 6 大类约束，系统化落地到本项目 `rules/` + `algorithms/` + `configs/` + `tests/`。

## 规格速查表

| # | 规格项 | POC 阶段量化值 | 宽度 | RIB1 & RIB5 数量/节距 | RIB2/3/4 数量/节距 | 项目落点 |
|---|-------|---------------|------|----------------------|-------------------|---------|
| 1 | 主沟 | 10 mm | 8-12 mm | — 3-4 条合计（70% 为 4 条）— | — | `algorithms/detection/` + `rules/rule1to5.py`（横图拼接按主沟对齐） |
| 2 | 横沟 | R1/5 → 3.5 mm；其余 → 1.8 mm | 1.5-5 mm（R1/5 常 3-5 mm；R2/3/4 常 1.5-2 mm） | 一般 1 个（计海陆比时有帮助） | 各 ≤ 1 个 | `algorithms/detection/groove_intersection.py`、`rules/scoring/land_sea_ratio.py` |
| 3 | 横向钢片 | 0.6 mm | 0.4-0.8 mm | 0-2 个 | 0-3 个 | 位置：两横沟之间花纹块中均分 |
| 4 | 纵向钢片 & 纵向细沟 | 1 mm | 钢片 0.4-0.8 mm；细沟 1-2 mm | 0-1 个 | 0-2 个 | `algorithms/stitching/rib_continuity_stitch.py` 相关 |
| 5 | 钢片 & 横沟连续性 | — | — | 两 RIB 间连续性占比 **60%-70%**（生成 100 张要有 60-70 张满足） | `algorithms/detection/pattern_continuity.py` + `rules/rule13.py` / `rule19.py` |
| 6 | 海陆比 | — | — | 1 个节距 TDW 范围内 (黑+灰)/(TDW×节距) 在 **28%-35%** | `rules/scoring/land_sea_ratio.py` |

> 程序处理的两条原则（来自规格图右下）：
> 1) 主沟/横沟/钢片/连续性 → **生成时**按上表量化指标做约束
> 2) 海陆比 → **生成后**识别花纹要素 → 线条扩展成面 → 计算黑色面积+灰色面积 → 套公式算海陆比 → 不符合的图片**舍弃**

## What This Skill Produces

对每一个规格项 / 每一次规格表更新，产出：

1. **`plans/rules/<rule_name>.md`**：遵循现有 plan 模板（见 `plans/rules/rule1to5.md`），含调用链路、涉及文件、实现步骤。
2. **`configs/` 中的 dataclass 或常量**：把量化阈值写成可配置项（例：`LAND_SEA_RATIO_MIN=0.28, LAND_SEA_RATIO_MAX=0.35`）。
3. **`rules/<rule_name>.py` 中间层**：遵循 `/memories/repo/rule_implementation_pattern.md` 的 `process_<rule>(task_id, conf) -> Tuple[bool, dict]` 签名与返回结构。
4. **`algorithms/` 中的纯算法函数**：检测 / 评分 / 拼接核心。
5. **`tests/unittests/rules/` 单测**：断言量化边界（28%/35%、60%/70%、RIB 数量上下限）。

## Procedure

### Step 1 — 识别规格项属于哪一类
- **生成期约束**（#1-#4）：转为 `configs/` 参数 + 传给 `algorithms/stitching/*` 或生成服务。
- **筛选期约束**（#5-#6）：转为 `rules/scoring/` 或 `rules/rule*.py` 的布尔判定（pass/fail）或分数。

### Step 2 — 映射到已有文件（先查再写）
先 `grep_search` 关键词避免重复实现，映射参考：

| 规格关键字 | 检索关键字 | 常见落点 |
|-----------|-----------|---------|
| 主沟 / main groove | `main_groove`, `rib_count` | `configs/user_config.py`, `algorithms/stitching/horizontal_stitch.py` |
| 横沟 / transverse groove | `groove_intersection`, `transverse` | `algorithms/detection/groove_intersection.py` |
| 横向钢片 / sipe | `sipe`, `steel` | algorithms/detection（可能需新增） |
| 纵向钢片 & 细沟 | `rib_continuity`, `fine_groove` | `algorithms/stitching/rib_continuity_stitch.py` |
| 钢片&横沟连续性 | `pattern_continuity`, `continuity` | `algorithms/detection/pattern_continuity.py`, `rules/rule13.py` |
| 海陆比 | `land_sea_ratio`, `land_sea` | `rules/scoring/land_sea_ratio.py` |

### Step 3 — 写入配置（单一事实源）
所有量化阈值必须经过 `configs/`，**不要**在 `rules/` 或 `algorithms/` 里硬编码。命名约定：
- 范围类：`<METRIC>_MIN` / `<METRIC>_MAX`（如 `LAND_SEA_RATIO_MIN=0.28`）
- 计数类：`<METRIC>_COUNT_MIN` / `<METRIC>_COUNT_MAX`（per-rib 用 dict：`{"RIB1":(0,2), "RIB2":(0,3), ...}`）
- POC 阶段参数：`POC_<ITEM>_MM`（如 `POC_MAIN_GROOVE_MM=10`）

### Step 4 — 写规则中间层
严格遵循 `/memories/repo/rule_implementation_pattern.md`：`process_<rule_name>(task_id, conf)` → 目录遍历 → 调 algorithms → 聚合 summary。海陆比/连续性这类筛选规则，**不符合即舍弃图片**（参考处理原则 2），在 summary 中记录 `discarded_count`。

### Step 5 — 写单元测试（量化边界是必测点）
在 `tests/unittests/rules/` 新增测试，最少覆盖：
- **边界值**：28.0%（应通过）、27.9%（应拒绝）、35.0%（应通过）、35.1%（应拒绝）
- **连续性比例**：生成 100 张 mock，断言通过率落在 60-70%
- **per-rib 数量**：RIB1 放 3 个横向钢片（上限 2） → 应失败
- 测试数据放 `tests/datasets/task_id_<rule_name>/`

### Step 6 — 串到 postprocessor
在 `services/postprocessor.py` 的 9 阶段流程里找到合适阶段（通常"小图打分"或"横图打分"）挂上规则；更新 `configs/postprocessor_config.py`。

## When to Load Reference Files

- 要写新 rule 的实现计划 → 参考 `plans/rules/rule1to5.md` 的章节结构
- 要实现海陆比 / 连续性算法 → 查 `algorithms/detection/pattern_continuity.py` 与 `rules/scoring/land_sea_ratio.py`
- 返回格式不确定 → 参考仓库记忆 `/memories/repo/rule_implementation_pattern.md`

## Completion Checklist

- [ ] 规格项的每个数值都在 `configs/` 里有命名常量（没有硬编码）
- [ ] `rules/<rule>.py` 返回结构匹配仓库通用 schema（`directories` + `summary`）
- [ ] 单测覆盖量化边界的 ±0.1 / ±1 两侧
- [ ] 筛选类规则记录 `discarded_count` 并能从 summary 反查被舍弃图片
- [ ] 在 `plans/rules/` 留下本次落地的 md 计划
- [ ] `services/postprocessor.py` 9 阶段中确认规则的挂载点

## Anti-patterns

- ❌ 把 `0.28 / 0.35 / 60 / 70` 这类阈值直接写进算法函数
- ❌ 把 per-rib 数量约束写死成 5 个 if 分支（应用 dict 驱动 RIB1-5）
- ❌ 海陆比不符合时仍保留图片（规格要求**舍弃**）
- ❌ 在 algorithms 层直接读文件/写文件（只做纯算法，I/O 交给 rules 层）
- ❌ 跳过 `plans/rules/*.md` 直接写代码（本仓库规范要求先出计划）
