# compute_land_sea_ratio

## 功能概述

`compute_land_sea_ratio` 是海陆比评分算法的核心入口，用于计算轮胎花纹样稿的海陆比（黑色区域与灰色区域占图像总面积的百分比），并按三级容差规则给出评分。

海陆比是评估轮胎花纹排水性能的重要指标。黑色区域代表深沟槽，灰色区域代表浅沟槽或细花纹，两者之和与总面积的比值即为海陆比。

本模块属于算法层（`src/core/scoring/`），不保存文件，不接收 task_id 或输出路径，不承载业务评分以外的逻辑。

---

## 函数入口

```python
from src.core.scoring.land_sea_ratio import compute_land_sea_ratio
```

---

## 函数签名

```python
def compute_land_sea_ratio(
    image: np.ndarray,
    target_min: float = 28.0,
    target_max: float = 35.0,
    margin: float = 5.0,
    is_debug: bool = False,
) -> tuple[int, float, str, np.ndarray | None]:
```

---

## 输入参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `image` | `np.ndarray` | 必填 | 输入 BGR 图像，形状必须为 `(H, W, 3)` |
| `target_min` | `float` | `28.0` | 海陆比目标区间下界（百分比）。例如 28.0 表示 28% |
| `target_max` | `float` | `35.0` | 海陆比目标区间上界（百分比）。必须大于 `target_min` |
| `margin` | `float` | `5.0` | 容差宽度（百分比）。落在容差范围内得 1 分，超出得 0 分 |
| `is_debug` | `bool` | `False` | 是否输出可视化调试图像 |

---

## 输出参数

函数返回一个包含四个元素的 tuple：

| 位置 | 名称 | 类型 | 说明 |
|---|---|---|---|
| 0 | `score` | `int` | 评分结果：`2`（优秀）、`1`（合格）、`0`（不合格） |
| 1 | `ratio_percent` | `float` | 实际海陆比百分比，保留两位小数。例如 `24.72` 表示 24.72% |
| 2 | `vis_name` | `str` | 建议的可视化文件名。非 debug 模式返回空字符串 `""` |
| 3 | `vis_image` | `np.ndarray` 或 `None` | 可视化图像（BGR）。非 debug 模式返回 `None` |

---

## 评分规则

三级容差评分规则如下：

| 评分 | 级别 | 判定条件 |
|---|---|---|
| 2 | 优秀 | `target_min <= ratio_percent <= target_max` |
| 1 | 合格 | `(target_min - margin) <= ratio_percent < target_min` 或 `target_max < ratio_percent <= (target_max + margin)` |
| 0 | 不合格 | 其余情况（超出容差范围） |

以默认参数为例（target_min=28, target_max=35, margin=5）：
- 海陆比在 `[28%, 35%]` 内 → 2 分
- 海陆比在 `[23%, 28%)` 或 `(35%, 40%]` 内 → 1 分
- 海陆比低于 23% 或高于 40% → 0 分

---

## 算法逻辑

计算流程分为四步：

**第一步：灰度转换**

将输入 BGR 图像转换为单通道灰度图，后续所有像素统计基于灰度值进行。

**第二步：像素面积统计**

- 黑色区域：灰度值在 `[0, 50]` 范围内的像素，统计其数量（`black_area`）
- 灰色区域：灰度值在 `[51, 200]` 范围内的像素，统计其数量（`gray_area`）
- 总面积：图像宽 × 高（像素数）

**第三步：海陆比计算**

```
ratio_percent = (black_area + gray_area) / total_area × 100
```

结果保留两位小数。

**第四步：三级容差评分**

对照评分规则（见上节）对 `ratio_percent` 进行评分。

**可选：debug 可视化**

当 `is_debug=True` 时，在原图上叠加颜色标注：
- 黑色区域叠加红色半透明覆盖层（alpha=0.5）
- 灰色区域叠加绿色半透明覆盖层（alpha=0.5）
- 左上角绘制海陆比百分比和评分文字（字体大小自适应图像尺寸，文字颜色根据背景亮度自动选黑/白）

---

## 异常处理

| 异常类 | 触发条件 |
|---|---|
| `InputDataError` | `image` 为 `None`，或非 `np.ndarray`，或形状不是 `(H, W, 3)` |
| `InputDataError` | `target_min < 0`，或 `target_max <= target_min`，或 `margin < 0` |
| `RuntimeProcessError` | 内部 cv2 计算失败，原始异常挂在 `__cause__` 上 |
| `RuntimeProcessError` | debug 可视化生成失败，原始异常挂在 `__cause__` 上 |

---

## 使用示例

### 基础用法

```python
import cv2
from src.core.scoring.land_sea_ratio import compute_land_sea_ratio

image = cv2.imread("combine_horizontal/sample.png")

score, ratio_percent, _, _ = compute_land_sea_ratio(image)
print(f"海陆比: {ratio_percent}%")
print(f"评分: {score}")
```

### 自定义评分阈值

```python
score, ratio_percent, _, _ = compute_land_sea_ratio(
    image,
    target_min=25.0,
    target_max=38.0,
    margin=3.0,
)
```

### 生成 debug 可视化图像

```python
score, ratio_percent, vis_name, vis_image = compute_land_sea_ratio(
    image,
    is_debug=True,
)

# 由调用方决定是否保存，算法层不保存文件
if vis_image is not None:
    output_path = pathlib.Path("output") / vis_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), vis_image)
```

---

## 内部辅助函数

以下函数为算法内部函数，由 `compute_land_sea_ratio` 调用，不作为公开 API。

### `_compute_black_area(gray: np.ndarray) -> int`

统计灰度值在 `[0, 50]` 范围内的像素数（黑色区域）。

### `_compute_gray_area(gray: np.ndarray) -> int`

统计灰度值在 `[51, 200]` 范围内的像素数（灰色区域）。

### `_score(ratio_percent, target_min, target_max, margin) -> int`

根据三级容差规则计算评分。

### `_draw_debug_image(image, gray, ratio_percent, score) -> np.ndarray`

生成带颜色叠加标注的可视化图像。与老架构 `rule13.visualize_score()` 实现逻辑等价，保证像素级一致。

---

## 测试覆盖

| 测试类 | 覆盖内容 |
|---|---|
| `TestComputeLandSeaRatioApi` | 输入边界：None、非 ndarray、灰度图、参数非法 |
| `TestScoring` | 三级评分：优秀/合格（上下容差）/不合格，纯白图边界 |
| `TestBlackGrayArea` | 黑色/灰色区域边界值（灰度值 50/51、200/201） |
| `TestDebugVisualization` | is_debug=True/False 的返回类型、文件名、图像形状 |
| `TestRuntimeErrors` | 内部计算异常和 debug 异常的 RuntimeProcessError 包装 |
| `TestRealImages` | 真实大图评分等价性验证、与 wise_image_dev1 像素级比对 |

覆盖率：`src/core/scoring/land_sea_ratio.py` 为 **100%**。

---

## 迁移说明

本模块从老架构 `feature/dev` 的 `rules/scoring/land_sea_ratio.py` 迁移而来。

主要变更：

| 项目 | 老架构 | 新架构 |
|---|---|---|
| 模块路径 | `rules.scoring.land_sea_ratio` | `src.core.scoring.land_sea_ratio` |
| 函数入参 | `(img, conf: dict)` | 显式参数（`target_min`, `target_max`, `margin`） |
| 函数出参 | `(score: int, details: dict)` | `(score, ratio_percent, vis_name, vis_image)` |
| 可视化 | 由 `rule13.visualize_score()` 调用 `cv2.imwrite` 保存 | `is_debug=True` 时返回 ndarray，由调用方保存 |
| 文件操作 | 算法层包含 `Path`、`json.dump` 等 | 算法层无任何文件 I/O |
| task_id | 部分函数传入 task_id | 不存在 |
