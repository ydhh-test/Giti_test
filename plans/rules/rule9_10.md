# Rule 9 & 10: 横向钢片检测与位置评分

## 目标

新增 `rules/rule9_10.py` 中间层 + `algorithms/detection/sipe_detection.py` 算法层，
检测小图（128×128）中横向细线条（钢片）的数量和位置，按 RIB 类型评分。

## 需求

| 需求 | 描述 | 评分 |
|------|------|------|
| 9 | 横向钢片数量：center(RIB1/5) 0-2 个，side(RIB2/3/4) 0-3 个 | 4 分（二值制） |
| 10 | 横向钢片位置：均分两横沟之间花纹块 | 4 分（统一给分） |

POC 阶段参数：钢片宽度 0.6mm（范围 0.4-0.8mm），像素密度 7.1px/mm。

## 调用链路

```
services/postprocessor.py::_small_image_score()   ← 暂未挂载
  └─ rules/rule9_10.py::process_horizontal_sipes(task_id, conf)
       ├─ 遍历 center_inf / side_inf 目录
       ├─ 逐张调用 algorithms/detection/sipe_detection.py::detect_horizontal_sipes()
       │    ├─ 预处理：灰度 → 高斯模糊 → 自适应二值化
       │    ├─ 横沟锚点：复用 groove_intersection._analyze_grooves()
       │    ├─ 钢片检测：水平投影 + 宽度分类
       │    ├─ 需求9评分：_score_sipe_count()
       │    ├─ 需求10评分：_score_sipe_position()
       │    └─ 调试图：_draw_debug_image()
       ├─ 保存 {stem}_debug.png
       ├─ 写 results.json
       └─ 返回 {task_id, directories, summary}
```

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `configs/rules_config.py` | 修改 | 新增 `HorizontalSipesConfig`，注册到 `BusinessRules` |
| `algorithms/detection/sipe_detection.py` | 新建 | 钢片检测 + 位置评分算法 |
| `algorithms/detection/groove_intersection.py` | 复用 | import `_analyze_grooves` 做横沟锚点 |
| `rules/rule9_10.py` | 新建 | 中间层 |
| `tests/unittests/algorithms/detection/test_sipe_detection.py` | 新建 | 算法单测 |
| `tests/unittests/rules/test_rule9_10.py` | 新建 | 中间层单测 |

## 目录关系

```
.results/task_id_{task_id}/
├── center_inf/                       ← 输入（推理输出，RIB1/5）
├── side_inf/                         ← 输入（推理输出，RIB2/3/4）
└── detect_horizontal_sipes/          ← 输出
    ├── center/
    │   ├── {stem}_debug.png
    │   └── results.json
    └── side/
        ├── {stem}_debug.png
        └── results.json
```

## 算法设计

### 宽度分类

| 类型 | 宽度 (mm) | @7.1px/mm | 分类 |
|------|----------|-----------|------|
| 横沟 | 1.5-5mm | ≥11px | 分区锚点 |
| 钢片 | 0.4-0.8mm | 3-6px | 计数+位置评分 |
| 噪声 | <0.4mm | <3px | 忽略 |

### 需求9评分规则

二值制：`sipe_count ∈ [0, max_count]` → 4 分，否则 0 分。

### 需求10评分规则

1. 0 根钢片 → 4 分
2. 花纹块 = 横沟 + 图像边缘构成的区间
3. 每块内 K 根钢片，理想间距 = `block_height / (K+1)`
4. 每根偏差 ≤ `理想间距 × 0.3` → 通过
5. **所有块均通过** → 4 分；任一不通过 → 0 分

## 配置参数（HorizontalSipesConfig）

```python
sipe_width_mm:        {"center": 0.6, "side": 0.6}
sipe_width_range_mm:  [0.4, 0.8]
groove_min_width_mm:  {"center": 3.5, "side": 1.8}
pixel_per_mm:         7.1
sipe_count_max:       {"center": 2, "side": 3}
score_sipe_count:     4
score_sipe_position:  4
position_tolerance:   0.3
rib_label:            {"center": "RIB1/5", "side": "RIB2/3/4"}
```

## 返回格式

```python
# 算法层 detect_horizontal_sipes() 返回
(score, {
    "rib_type": "RIB1/5",
    "sipe_count": 2,
    "sipe_positions": [32.0, 96.0],
    "groove_count": 1,
    "groove_positions": [64.0],
    "is_valid": True,
    "score_req9": 4.0,
    "score_req10": 4.0,
    "debug_image": ndarray,
})

# 中间层 process_horizontal_sipes() 返回
(True, {
    "task_id": "xxx",
    "directories": {
        "center_inf": {
            "total_count": 10,
            "processed_count": 10,
            "success_count": 9,
            "failed_count": 1,
            "skipped_count": 0,
            "total_score": 72.0,
            "images": { ... }
        }
    },
    "summary": { ... }
})
```
