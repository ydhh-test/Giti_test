# rule13.py 横图打分中间层实施计划

**创建日期:** 2026-03-11
**状态:** 待实施
**负责人:** 研发团队

---

## 一、模块定位

| 项目 | 说明 |
|------|------|
| **模块名** | `rules/rule13.py` |
| **职责** | 横图打分中间层 |
| **输入目录** | `combine_horizontal` (横图拼接后的输出) |
| **核心算法** | `rules/scoring/land_sea_ratio.py::compute_land_sea_ratio` |
| **参考模板** | `rule6_1.py` (图案连续性检测中间层) |

---

## 二、文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `rules/rule13.py` | **新建** | 横图打分中间层主模块 |
| `configs/user_config.py` | **修改** | 添加 `horizontal_image_score_conf` 默认配置 |
| `services/postprocessor.py` | **修改** | 实现 `_horizontal_image_score` 函数，调用 `rule13.process_horizontal_image_score` |
| `services/postprocessor.py` | **修改** | 移除 `_calculate_total_score` 中的 `compute_land_sea_ratio` 调用 |
| `tests/unittests/rules/test_rule13.py` | **新建** | rule13 单元测试 |

---

## 三、详细实施步骤

### Step 1: 创建 `rules/rule13.py` 模块框架

**文件路径:** `rules/rule13.py`

**模块结构:**
```python
# -*- coding: utf-8 -*-
"""
rule13: 横图打分中间层

功能:
- 接收 postprocessor 的调用
- 循环 combine_horizontal 目录中的所有图片
- 调用 compute_land_sea_ratio() 进行海陆比评分
- 保存评分结果和可视化结果

目录关系:
- 输入：.results/task_id_{task_id}/combine_horizontal/{image_name}.png
- 可视化输出：.results/task_id_{task_id}/rule13/{image_name}.png
- 评分结果 JSON: .results/task_id_{task_id}/scores/rule13/{image_name}.json
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
import cv2
import json

from utils.logger import get_logger

logger = get_logger("rule13")


def process_horizontal_image_score(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    横图打分主入口

    参数:
        task_id: 任务 ID
        conf: 配置字典
            - input_dir: 输入目录名 (可选，默认 "combine_horizontal")
            - land_sea_ratio: 海陆比算法配置
            - visualize: 是否生成可视化 (可选，默认 True)
            - output_base_dir: 输出基础目录 (可选，默认 ".results")

    返回:
        (True, 详细统计字典) 或 (False, 错误信息)
    """
    ...


def process_single_image(
    image_path: Path,
    task_id: str,
    conf: dict,
    image_id: int
) -> Tuple[bool, Dict[str, Any]]:
    """
    对单张图片进行海陆比评分

    参数:
        image_path: 图片路径
        task_id: 任务 ID
        conf: 配置字典
        image_id: 图片序号 (用于日志和追踪)

    返回:
        (True, 单张图片评分结果) 或 (False, 错误信息)
    """
    ...


def visualize_score(image: np.ndarray, score: int, ratio: float, output_path: Path) -> None:
    """
    在新图上标注海陆比分数和颜色

    参数:
        image: 输入图片
        score: 评分 (0/1/2)
        ratio: 海陆比值
        output_path: 输出路径
    """
    ...


def save_score_json(score_data: dict, output_path: Path) -> None:
    """
    保存单张图片的评分结果为 JSON 文件

    参数:
        score_data: 评分数据字典
        output_path: JSON 文件输出路径
    """
    ...


# ========== 辅助函数 ==========

def _get_image_files(dir_path: Path) -> List[Path]:
    """获取目录内所有图片文件，按文件名排序"""
    ...


def _aggregate_summary(image_results: List[Dict[str, Any]]) -> dict:
    """聚合所有图片的统计信息"""
    ...
```

---

### Step 2: 实现 `process_horizontal_image_score` 主入口

**职责:** 类似 `rule6_1::process_pattern_continuity`

**核心流程:**
1. 从 conf 读取配置参数 (`input_dir`, `land_sea_ratio`, `visualize`, `output_base_dir`)
2. 构建输入目录路径：`.results/task_id_{task_id}/{input_dir}/`
3. 检查目录是否存在
4. 获取图片列表
5. 循环调用 `process_single_image` 处理每张图片
6. 聚合统计信息并返回

**返回格式 (参考 rule6_1):**
```python
(True, {
    "task_id": task_id,
    "directories": {
        "combine_horizontal": {
            "total_count": 10,
            "scored_count": 10,
            "failed_count": 0,
            "total_score": 18,
            "images": {
                "sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png": {
                    "score": 2,
                    "land_sea_ratio": 30.5,
                    "status": "success",
                    "image_id": "0",
                    "vis_path": ".results/task_id_{task_id}/rule13/sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png",
                    "json_path": ".results/task_id_{task_id}/scores/rule13/sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.json"
                },
                ...
            }
        }
    },
    "summary": {
        "total_images": 10,
        "total_scored": 10,
        "total_failed": 0,
        "total_score": 18
    }
})
```

---

### Step 3: 实现 `process_single_image` 单图处理

**职责:** 单张图片的海陆比评分 + 可视化 + JSON 保存

**核心流程:**
1. 读取图片 (使用 `cv2.imread`)
2. 调用 `compute_land_sea_ratio(img, land_sea_ratio_conf)` 获取 `(score, details)`
3. 构建输出路径:
   - 可视化：`.results/task_id_{task_id}/rule13/{image_name}`
   - JSON: `.results/task_id_{task_id}/scores/rule13/{image_name}.json`
4. 如果 `visualize=True`:
   - 调用 `visualize_score()` 创建标注图
   - 保存到可视化路径
5. 调用 `save_score_json()` 保存评分结果 JSON
6. 返回评分结果

**返回格式:**
```python
(True, {
    "image_name": "sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png",
    "image_id": "0",
    "score": 2,
    "land_sea_ratio": 30.5,
    "status": "success",
    "details": {...},  # compute_land_sea_ratio 返回的 details
    "vis_path": ".results/task_id_{task_id}/rule13/sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png",
    "json_path": ".results/task_id_{task_id}/scores/rule13/sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.json"
})
```

---

### Step 4: 实现 `visualize_score` 可视化函数

**职责:** 在新图上标注海陆比分数，并用颜色标识黑色和灰色区域

**参数:**
- `image`: 输入图片 (numpy array)
- `score`: 评分 (0/1/2)
- `ratio`: 海陆比值 (float)
- `output_path`: 输出路径

**可视化设计:**

#### 4.1 区域颜色叠加

| 区域 | 来源 | 颜色 (RGBA) | 说明 |
|------|------|-------------|------|
| **黑色区域** | `compute_black_area` 返回的区域 | 红色 `(255, 0, 0, 128)` | 深沟槽 |
| **灰色区域** | `compute_gray_area` 返回的区域 | 绿色 `(0, 255, 0, 128)` | 浅沟槽/细花 |
| **白色区域** | - | 不标识 | 背景 |

#### 4.2 标注内容

| 文字 | 内容示例 | 位置 |
|------|----------|------|
| 海陆比 | `海陆比：30.5%` | 左上角 |
| 评分 | `评分：2` | 海陆比下方 |

#### 4.3 样式要求

| 属性 | 要求 |
|------|------|
| 字体大小 | 自适应 (根据图片尺寸动态调整) |
| 文字颜色 | 自适应 (根据背景深浅选择黑色或白色) |
| 文字位置 | 左上角 |

#### 4.4 实现思路

```python
def visualize_score(image: np.ndarray, score: int, ratio: float,
                    output_path: Path) -> None:
    """
    在新图上标注海陆比分数，并用颜色标识黑色和灰色区域

    流程:
    1. 创建图片副本
    2. 调用 compute_black_area 获取黑色区域掩码
    3. 调用 compute_gray_area 获取灰色区域掩码
    4. 在副本上叠加颜色层：
       - 黑色区域 → 红色半透明叠加
       - 灰色区域 → 绿色半透明叠加
    5. 计算自适应字体大小 (基于图片宽度/高度)
    6. 计算自适应文字颜色 (根据背景亮度)
    7. 在左上角绘制标注文字
    8. 保存结果
    """
    import cv2
    import numpy as np

    # Step 1: 创建副本
    vis_img = image.copy()

    # Step 2-3: 获取黑色和灰色区域掩码
    gray = cv2.cvtColor(vis_img, cv2.COLOR_BGR2GRAY) if len(vis_img.shape) == 3 else vis_img
    black_mask = cv2.inRange(gray, 0, 50)      # 黑色区域阈值
    gray_mask = cv2.inRange(gray, 51, 200)     # 灰色区域阈值

    # Step 4: 叠加颜色层
    # 红色叠加层 (黑色区域)
    red_overlay = np.zeros_like(vis_img)
    red_overlay[:, :] = (0, 0, 255)  # BGR 红色
    vis_img = cv2.addWeighted(vis_img, 1,
                              cv2.bitwise_and(red_overlay, red_overlay, mask=black_mask),
                              0.5, 0)

    # 绿色叠加层 (灰色区域)
    green_overlay = np.zeros_like(vis_img)
    green_overlay[:, :] = (0, 255, 0)  # BGR 绿色
    vis_img = cv2.addWeighted(vis_img, 1,
                              cv2.bitwise_and(green_overlay, green_overlay, mask=gray_mask),
                              0.5, 0)

    # Step 5: 自适应字体大小
    height, width = vis_img.shape[:2]
    font_scale = min(width, height) / 500  # 自适应系数

    # Step 6: 自适应文字颜色
    roi = gray[0:100, 0:200] if gray.shape[0] > 100 and gray.shape[1] > 200 else gray
    avg_brightness = np.mean(roi)
    text_color = (0, 0, 0) if avg_brightness > 128 else (255, 255, 255)

    # Step 7: 绘制标注文字
    text1 = f"海陆比：{ratio:.2f}%"
    text2 = f"评分：{score}"

    y_offset = int(30 * font_scale)
    cv2.putText(vis_img, text1, (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 2)
    cv2.putText(vis_img, text2, (10, int(y_offset * 2.5)),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 2)

    # Step 8: 保存结果
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), vis_img)
```

---

### Step 5: 实现 `save_score_json` JSON 保存函数

**职责:** 保存单张图片的评分结果为 JSON 文件

**参数:**
- `score_data`: 评分数据字典
- `output_path`: JSON 文件输出路径

**示例代码框架:**
```python
def save_score_json(score_data: dict, output_path: Path) -> None:
    """保存单张图片的评分结果为 JSON 文件"""
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入 JSON 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(score_data, f, indent=2, ensure_ascii=False)
```

---

### Step 6: 实现辅助函数

#### 6.1 `_get_image_files(dir_path: Path) -> List[Path]`

**职责:** 获取目录内所有图片文件，按文件名排序

```python
def _get_image_files(dir_path: Path) -> List[Path]:
    """获取目录内所有图片文件，按文件名排序"""
    extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    image_files = []
    for ext in extensions:
        image_files.extend(dir_path.glob(f"*{ext}"))
    return sorted(image_files, key=lambda x: x.name)
```

#### 6.2 `_aggregate_summary(image_results: List[Dict[str, Any]]) -> dict`

**职责:** 聚合所有图片的统计信息

```python
def _aggregate_summary(image_results: List[Dict[str, Any]]) -> dict:
    """聚合所有图片的统计信息"""
    total_count = len(image_results)
    scored_count = sum(1 for r in image_results if r.get("status") == "success")
    failed_count = total_count - scored_count
    total_score = sum(r.get("score", 0) for r in image_results if r.get("status") == "success")

    return {
        "total_images": total_count,
        "total_scored": scored_count,
        "total_failed": failed_count,
        "total_score": total_score
    }
```

---

### Step 7: 更新 `configs/user_config.py` 添加默认配置

**需要添加的配置:**

```python
# 横图打分配置
DEFAULT_HORIZONTAL_IMAGE_SCORE_CONF = {
    "input_dir": "combine_horizontal",
    "visualize": True,
    "output_base_dir": ".results",
    "land_sea_ratio": {
        "target_min": 28.0,
        "target_max": 35.0,
        "margin": 5.0
    }
}
```

---

### Step 8: 更新 `services/postprocessor.py`

#### 8.1 实现 `_horizontal_image_score`

```python
def _horizontal_image_score(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    横图打分阶段

    Args:
        task_id: 任务 ID
        conf: 横图打分配置

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from rules.rule13 import process_horizontal_image_score

    # 调用 rule13 中间层
    flag, details = process_horizontal_image_score(task_id, conf)

    if not flag:
        return False, {
            "err_msg": details.get("err_msg", "横图打分失败"),
            "task_id": task_id
        }

    # 提取图片数量信息
    summary = details.get("summary", {})
    return True, {
        "task_id": task_id,
        "horizontal_image_score_stats": details,
        "image_gen_number": summary.get("total_scored", 0),
        "total_score": summary.get("total_score", 0)
    }
```

#### 8.2 修改 `_calculate_total_score` (Stage 8)

**当前:** 调用了 `compute_land_sea_ratio`
**修改后:** 移除海陆比计算，只负责聚合已有评分

```python
def _calculate_total_score(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    统计总分阶段

    Args:
        task_id: 任务 ID
        conf: 评分配置

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    # TODO: 聚合前序阶段的评分结果
    # 不再调用 compute_land_sea_ratio
    return True, {"total_score": 0, "task_id": task_id}
```

---

### Step 9: 编写单元测试

**文件路径:** `tests/unittests/rules/test_rule13.py`

**测试用例清单:**

| 测试项 | 描述 | 清理 |
|--------|------|------|
| `test_get_image_files` | 测试图片文件获取 | 是 |
| `test_aggregate_summary` | 测试统计聚合 | 是 |
| `test_process_horizontal_image_score_nonexistent_dir` | 测试目录不存在的情况 | 是 |
| `test_process_horizontal_image_score_empty_dir` | 测试输入目录为空的情况 | 是 |
| `test_visualize_score` | 测试可视化输出函数 | 是 |
| `test_save_score_json` | 测试 JSON 保存函数 | 是 |
| `test_process_single_image` | 测试单张图片处理 | 是 |
| `test_process_horizontal_image_score_full` | **总的正例测试，放最后执行** | **否** |

**总的正例测试说明:**
- 创建完整的测试环境 (模拟 task_id 目录结构 + 测试图片)
- 执行完整的横图打分流程
- 验证所有输出 (返回值、可视化文件、每张图片的 JSON)
- **测试执行后不清理**，便于手动验证结果

---

## 四、数据流图

```
postprocessor (Stage 6: 横图打分)
         │
         ▼
    _horizontal_image_score(task_id, conf)
         │
         ▼
    rule13.process_horizontal_image_score(task_id, conf)
         │
         ├── 读取配置：input_dir, land_sea_ratio, visualize
         │
         ▼
    构建输入目录：.results/task_id_{task_id}/combine_horizontal/
         │
         ▼
    获取图片列表
         │
         ▼
    循环处理每张图片 ────────────────────────────────┐
         │                                          │
         ▼                                          │
    process_single_image(image_path, image_id)      │
         │                                          │
         ├── cv2.imread(image_path)                 │
         │                                          │
         ▼                                          │
    compute_land_sea_ratio(img, conf)               │
         │                                          │
         ├── 返回 (score, details)                  │
         │                                          │
         ▼                                          │
    如果 visualize=True:                            │
         ├── visualize_score()                      │
         │   └── 保存：.results/.../rule13/         │
         │       sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png │
         │                                          │
         ▼                                          │
    save_score_json()                               │
         └── 保存：.results/.../scores/rule13/      │
             sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.json    │
                                                    │
         │                                          │
         ▼                                          │
    记录评分结果 ────────────────────────────────────┘
         │
         ▼
    聚合统计信息
         │
         ▼
    返回 (True, {directories, summary})
```

---

## 五、输出目录结构

```
.results/task_id_1778457600/
├── combine_horizontal/                    # 输入目录 (横图拼接输出)
│   ├── sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png
│   ├── sym_0_r1_0_r2_0_r3_0_r4_0_r5_1.png
│   └── ...
├── rule13/                                # 可视化输出目录
│   ├── sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png  (带红色/绿色叠加层 + 标注文字)
│   ├── sym_0_r1_0_r2_0_r3_0_r4_0_r5_1.png
│   └── ...
└── scores/
    └── rule13/                            # 评分结果 JSON 目录
        ├── sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.json
        ├── sym_0_r1_0_r2_0_r3_0_r4_0_r5_1.json
        └── ...
```

---

## 六、单张图片 JSON 格式

**文件:** `.results/task_id_{task_id}/scores/rule13/{image_name}.json`

```json
{
    "task_id": "1778457600",
    "image_name": "sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png",
    "image_id": "0",
    "score": 2,
    "land_sea_ratio": 30.5,
    "status": "success",
    "details": {
        "ratio_value": 30.5,
        "target_range": "[28.0%, 35.0%]",
        "black_area": 10000,
        "gray_area": 20000,
        "total_area": 100000
    },
    "vis_path": ".results/task_id_1778457600/rule13/sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png"
}
```

---

## 七、可视化效果示意

```
输入图片 (combine_horizontal 中的原图)
         │
         ▼
┌─────────────────────────────────────────┐
│ 海陆比：30.5%                            │ ← 左上角标注文字
│ 评分：2                                  │
│                                         │
│    [红色区域=深沟槽]                     │
│    [绿色区域=浅沟槽/细花]                 │
│         ...                             │
│                                         │
└─────────────────────────────────────────┘
         │
         ▼
输出到 rule13/{image_name}.png
```

---

## 八、风险与注意事项

| 风险点 | 说明 | 缓解措施 |
|--------|------|----------|
| **图片读取失败** | 某些图片可能损坏或格式不支持 | 单图失败不影响其他图片，记录错误继续处理 |
| **目录为空** | combine_horizontal 可能没有图片 | 返回空统计，不报错 |
| **配置缺失** | land_sea_ratio 配置可能不完整 | 使用默认值，参考 `compute_land_sea_ratio` 的默认值 |
| **可视化性能** | 保存可视化可能影响性能 | visualize 默认为 True，但用户可以关闭 |
| **JSON 写入失败** | 磁盘空间不足或权限问题 | 单图 JSON 失败不影响其他图片 |
| **文字自适应效果** | 极端尺寸图片可能导致文字过大或过小 | 设置字体大小的上下限 |

---

## 九、总结

最终计划的核心变更：

1. **创建 `rule13.py`** - 作为横图打分的中间层，遵循 `rule6_1.py` 的架构模式
2. **循环 `combine_horizontal` 目录** - 对所有横图拼接后的图片执行海陆比算法
3. **可视化输出**:
   - 用**红色**标识黑色区域 (深沟槽)
   - 用**绿色**标识灰色区域 (浅沟槽/细花)
   - 左上角标注海陆比值和评分 (只写分值)
   - 字体大小和文字颜色自适应
4. **评分结果 JSON** - 每张图片一个独立的 JSON 文件：`scores/rule13/{image_name}.json`
5. **Stage 8 调整** - 移除重复的海陆比调用，只负责聚合
6. **单元测试** - 总的正例测试执行后不清理，便于手动验证

---

## 十、头脑风暴记录

### 决策 1: rule13.py 职责定位
- **确认:** 类似于 `rule6_1.py` (图案连续性检测中间层)
- **输入目录:** `combine_horizontal` (横图拼接后的输出)
- **执行对象:** 所有横图拼接后的图片

### 决策 2: 可视化输出格式
- **确认:** 在新图上标注海陆比分数和颜色
- **保存路径:** `.results/task_id_{task_id}/rule13/{image_name}.png`
- **不区分:** center 和 side (横向拼接后的图不区分)

### 决策 3: 评分结果保存
- **确认:** 每张图片一个独立的 JSON 文件
- **保存路径:** `.results/task_id_{task_id}/scores/rule13/{image_name}.json`

### 决策 4: Stage 8 职责
- **确认:** Stage 8 不再调用 `compute_land_sea_ratio`，只负责聚合已有评分

### 决策 5: 测试用例清理
- **确认:** 总的正例测试执行后不清理，便于手动验证

### 决策 6: 可视化颜色映射
- **黑色区域 (compute_black_area):** 红色
- **灰色区域 (compute_gray_area):** 绿色
- **白色区域:** 不需要标识

### 决策 7: 可视化标注样式
- **字体大小:** 自适应 (根据图片尺寸)
- **文字颜色:** 自适应 (根据背景亮度)
- **文字位置:** 左上角
- **标注内容:** 海陆比值 + 评分 (只写分值，不写"优秀"等描述)
