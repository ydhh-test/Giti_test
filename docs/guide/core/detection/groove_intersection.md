# 横沟检测算法

`src.core.detection.groove_intersection` 提供 Rule 8 使用的底层图像检测能力，用于统计一张轮胎小图中的横向粗线条数量，并同时输出横沟与纵向线条的交叉点数量，供后续 Rule 14 使用。

该模块属于 `src.core` 算法层，只负责从内存中的 BGR 图像提取算法特征。它不负责规则评分、不保存文件、不读写 `.results/`，也不处理 `task_id`、规则目录或 pipeline 调度。

## 适用场景

使用该算法时，输入应是一张已经读入内存的 BGR 小图。

典型调用方包括：

- 小图评估规则层：根据 `groove_count` 判断 Rule 8，根据 `intersection_count` 判断 Rule 14。
- 调试工具：在 `is_debug=True` 时获取染色图，用于人工比对和排查误判。
- 单元测试：构造合成二值图或真实轮胎小图，验证横沟聚合和交叉点统计逻辑。

不适合在该模块内完成的工作：

- 规则评分，例如 Rule 8 返回多少分、Rule 14 返回多少分。
- 图片删除、移动、重命名或保存。
- `.results/` 目录组织。
- `task_id`、接口协议、节点调度等上层流程概念。

## 快速开始

```python
import cv2
import numpy as np

from src.core.detection.groove_intersection import detect_transverse_grooves

buf = np.fromfile("small_tire.png", dtype=np.uint8)
image = cv2.imdecode(buf, cv2.IMREAD_COLOR)

groove_count, intersection_count, _, _ = detect_transverse_grooves(
    image,
    image_type="center",
)

print(groove_count, intersection_count)
```

Windows 中文路径下，推荐使用 `np.fromfile()` 和 `cv2.imdecode()` 读取图片，避免 `cv2.imread()` 对非 ASCII 路径支持不稳定的问题。

## API 入口

### `detect_transverse_grooves`

```python
detect_transverse_grooves(
    image: np.ndarray,
    image_type: str,
    pixel_per_mm: float = 7.1,
    is_debug: bool = False,
) -> tuple[int, int, str, np.ndarray | None]
```

检测 BGR 小图中的横沟数量，并统计横沟与纵向线条的交叉点数量。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `image` | `np.ndarray` | 必填 | 输入 BGR 图像，形状必须为 `(H, W, 3)`。不接受二维灰度图。 |
| `image_type` | `str` | 必填 | 小图类型，支持 `"center"` 或 `"side"`，大小写和前后空格会被归一化。 |
| `pixel_per_mm` | `float` | `7.1` | 像素密度，用于将横沟最小物理宽度换算为像素宽度。必须大于 0。 |
| `is_debug` | `bool` | `False` | 是否返回 debug 染色图。算法层只返回图像对象，不保存文件。 |

横沟最小物理宽度是算法内部常量：

| `image_type` | RIB 类型 | 最小横沟宽度 |
| --- | --- | --- |
| `center` | `RIB1/5` | `3.5 mm` |
| `side` | `RIB2/3/4` | `1.8 mm` |

这些值来自老架构 `feature/dev` 的 `TransverseGroovesConfig`，迁移后固定在算法内部，不通过公开 API 暴露。

### 返回值

函数返回显式 tuple：

```python
groove_count, intersection_count, vis_name, vis_image = detect_transverse_grooves(image, "center")
```

| 返回项 | 类型 | 说明 |
| --- | --- | --- |
| `groove_count` | `int` | 检测到的横沟数量。 |
| `intersection_count` | `int` | 横沟与纵向线条的交叉点数量。 |
| `vis_name` | `str` | debug 染色图建议文件名。`is_debug=False` 时为空字符串；`is_debug=True` 时为 `groove_intersection.png`。 |
| `vis_image` | `np.ndarray | None` | debug 染色图。`is_debug=False` 时为 `None`。 |

算法层不会返回 score、规则是否通过、保存路径或结果字典。横沟位置、RIB 类型和中间检测细节会写入日志，供调试定位使用。

## 算法逻辑

### 1. 输入校验

算法首先检查：

- `image` 不为 `None`。
- `image` 是 `np.ndarray`。
- `image` 是三通道 BGR 图。
- `image_type` 是 `"center"` 或 `"side"`。
- `pixel_per_mm > 0`。

如果输入不满足约定，会抛出 `InputDataError`。

### 2. 横沟宽度换算

算法根据小图类型选择横沟最小物理宽度：

```python
center: 3.5 mm
side: 1.8 mm
```

然后通过 `pixel_per_mm` 换算为像素宽度：

```python
groove_width_px = round(min_width_mm * pixel_per_mm)
```

默认 `pixel_per_mm=7.1` 时，`center` 的横沟阈值约为 `25 px`，`side` 的横沟阈值约为 `13 px`。

### 3. 灰度化与自适应二值化

算法将 BGR 图转为灰度图，并做轻量高斯模糊：

```python
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (3, 3), 0)
```

随后使用自适应阈值提取暗色沟槽前景：

```python
binary = cv2.adaptiveThreshold(
    blurred,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY_INV,
    blockSize=31,
    C=5,
)
```

效果是：暗色沟槽变为白色前景，浅色背景变为黑色背景。

### 4. 横沟区域识别

`_analyze_grooves()` 通过水平投影识别横向带状区域：

1. 逐行统计前景像素数。
2. 当前景像素数达到 `max(groove_width_px, image_width // 4)` 时，该行被视为候选横沟行。
3. 合并相邻候选行，允许最多 `3` 行空白间隔。
4. 过滤高度不足的行组，最小高度为 `max(3, groove_width_px // 5)`。
5. 返回横沟中心位置、横沟数量和横沟掩码。

### 5. 交叉点统计

`_count_intersections()` 统计横沟与纵向线条的交叉点数量。

对每条横沟，算法分别分析横沟上方和下方的列密度：

- 上下两侧都存在时，要求两侧列密度都达到约 `15%` 阈值。
- 只有一侧存在时，使用更严格的约 `25%` 阈值。
- 相邻热列会按 `5 px` 间隔容差合并为一个纵向线条聚类。
- 位于图像最左或最右边界的聚类会被过滤。
- 每个纵向聚类与每条横沟最多计为一个交叉点。

### 6. Debug 染色图

当 `is_debug=True` 时，函数额外返回染色图：

```python
groove_count, intersection_count, vis_name, vis_image = detect_transverse_grooves(
    image,
    image_type="side",
    is_debug=True,
)
```

返回内容：

- `vis_name == "groove_intersection.png"`
- `vis_image` 为 BGR 图像数组

染色图中：

- 检测到的横沟区域会叠加绿色半透明掩码。
- 每条横沟中心会绘制水平线。
- 左上角会显示 RIB 类型、横沟数量、交叉点数量和老架构兼容分数。

这里的分数只用于保持 debug 图与 `feature/dev` 老架构完全一致，不作为算法层公开输出。正式评分应由规则层根据 `groove_count` 和 `intersection_count` 计算。

## 示例

### 示例 1：基础横沟检测

```python
groove_count, intersection_count, _, _ = detect_transverse_grooves(
    image,
    image_type="center",
)

print(f"横沟数量: {groove_count}")
print(f"交叉点数量: {intersection_count}")
```

### 示例 2：side 小图检测

```python
groove_count, intersection_count, _, _ = detect_transverse_grooves(
    image,
    image_type="side",
)
```

`side` 类型使用 `RIB2/3/4` 的横沟宽度标准。

### 示例 3：生成 debug 图但不在算法层保存

```python
groove_count, intersection_count, vis_name, vis_image = detect_transverse_grooves(
    image,
    image_type="center",
    is_debug=True,
)

if vis_image is not None:
    cv2.imwrite(f".results/{vis_name}", vis_image)
```

保存路径由调用方决定。算法层只返回建议文件名和图像数组。

### 示例 4：规则层评分示意

```python
groove_count, intersection_count, _, _ = detect_transverse_grooves(image, "center")

rule8_pass = groove_count == 1
rule14_pass = intersection_count <= 2
```

评分逻辑不属于本算法文件职责，实际规则层可以根据配置决定分值。

## 等价性验证

本算法迁移自 `feature/dev` 的 `algorithms/detection/groove_intersection.py`。为了验证迁移等价性，测试数据目录中包含：

```text
tests/datasets/test_groove_intersection/
  center_inf/
  side_inf/
  wise_image_dev1/
  wise_image_dev2/
```

- `center_inf/` 与 `side_inf/` 保存老架构原始输入小图。
- `wise_image_dev1/` 保存老架构生成的 debug 染色图。
- `wise_image_dev2/` 保存新架构生成的 debug 染色图。

单元测试会对 dev1 与 dev2 染色图做 `np.array_equal()` 像素级比对。任意一张图不一致，都表示迁移后的 debug 产物与老架构不完全等价。

## 异常

| 异常 | 场景 |
| --- | --- |
| `InputDataError` | 输入图像为空、不是 ndarray、不是 BGR 三通道图，或 `image_type` / `pixel_per_mm` 不满足约定。 |
| `RuntimeProcessError` | OpenCV 处理、横沟分析、交叉点统计或 debug 图生成过程中出现运行时异常。 |

## 内部函数说明

| 函数 | 说明 |
| --- | --- |
| `_analyze_grooves` | 通过水平投影提取横沟中心位置、数量和掩码。 |
| `_count_intersections` | 基于横沟上下两侧列密度统计交叉点数量。 |
| `_skeletonize` | 保留的形态学骨架化工具函数，用于白盒验证和后续调试。 |
| `_legacy_debug_status` | 计算老架构兼容的 debug 标注状态，只用于生成等价染色图。 |
| `_draw_debug_image` | 在 BGR 原图上绘制横沟掩码、中心线和文字标注。 |

## 设计边界

- 算法层保留 `image_type`，因为 `center` 和 `side` 使用不同的横沟宽度标准。
- 算法层保留 `pixel_per_mm`，因为它是物理宽度换算到像素宽度的必要标定参数。
- 算法层不暴露 `groove_width_mm`，该值来自老架构稳定配置，迁移后作为内部常量。
- 算法层不暴露 `max_intersections`，该阈值属于 Rule 14 评分逻辑，应由规则层处理。
- 算法层不返回 score 或规则通过状态，只返回后续规则层需要的基础特征。