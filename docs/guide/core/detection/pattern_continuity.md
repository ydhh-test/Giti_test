# 图案连续性检测算法

`src.core.detection.pattern_continuity` 提供 Rule 6_1 使用的底层图像检测能力，用于判断一张轮胎小图的上边缘纹理与下边缘纹理是否能够连续对齐。

该模块属于 `src.core` 算法层，只负责从灰度图中提取边缘端点并判断连续性。它不负责评分、不删除图片、不保存可视化文件，也不处理任务目录、`task_id` 或 pipeline 调度。

## 适用场景

使用该算法时，输入应是一张已经读入内存的二维灰度图。

典型调用方包括：

- 小图评估规则层：根据 `is_continuous` 判断 Rule 6_1 是否通过。
- 调试工具：在 `is_debug=True` 时获取可视化图像，用于人工排查误判。
- 单元测试：构造合成图或真实轮胎小图，验证边缘端点匹配逻辑。

不适合在该模块内完成的工作：

- 规则评分，例如连续返回多少分。
- 图片删除、移动、重命名或保存。
- `.results/` 目录组织。
- `task_id`、接口协议、节点调度等上层流程概念。

## 快速开始

```python
import cv2
import numpy as np

from src.core.detection.pattern_continuity import detect_pattern_continuity

buf = np.fromfile("small_tire.png", dtype=np.uint8)
image = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)

is_continuous, vis_name, vis_image = detect_pattern_continuity(image)

if is_continuous:
	print("上下边缘图案连续")
else:
	print("上下边缘图案不连续")
```

Windows 中文路径下，推荐使用 `np.fromfile()` 和 `cv2.imdecode()` 读取图片，避免 `cv2.imread()` 对非 ASCII 路径支持不稳定的问题。

## API 入口

### `detect_pattern_continuity`

```python
detect_pattern_continuity(
	image: np.ndarray,
	threshold: int = 200,
	edge_height: int = 4,
	coarse_threshold: int = 5,
	fine_match_distance: int = 4,
	is_debug: bool = False,
) -> tuple[bool, str, np.ndarray | None]
```

检测灰度图上边缘和下边缘的深色纹理端点是否可以匹配。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `image` | `np.ndarray` | 必填 | 输入灰度图，形状必须为 `(H, W)`。不接受 BGR/RGB 三通道图。 |
| `threshold` | `int` | `200` | 固定二值化阈值。灰度值小于等于该阈值的像素会被视为深色纹理。 |
| `edge_height` | `int` | `4` | 从图片顶部和底部分别截取的边缘高度。图片高度必须至少为 `2 * edge_height`。 |
| `coarse_threshold` | `int` | `5` | 深色连通段宽度达到该值时视为粗线，否则视为细线。 |
| `fine_match_distance` | `int` | `4` | 细线与细线匹配时允许的最大水平距离。 |
| `is_debug` | `bool` | `False` | 是否返回 debug 可视化图像。算法层只返回图像对象，不保存文件。 |

### 返回值

函数返回显式 tuple：

```python
is_continuous, vis_name, vis_image = detect_pattern_continuity(image)
```

| 返回项 | 类型 | 说明 |
| --- | --- | --- |
| `is_continuous` | `bool` | 连续性判断结果。`True` 表示底边缘端点都能在上边缘找到匹配。 |
| `vis_name` | `str` | debug 可视化建议文件名。`is_debug=False` 时为空字符串；`is_debug=True` 时为 `pattern_continuity.png`。 |
| `vis_image` | `np.ndarray | None` | debug 可视化图像。`is_debug=False` 时为 `None`。 |

算法层不会返回评分、端点列表、匹配明细或保存路径。端点、匹配关系和未匹配结果会写入日志，供调试定位使用。

## 算法逻辑

### 1. 输入校验

算法首先检查：

- `image` 不为 `None`。
- `image` 是二维灰度图。
- 图片高度满足 `height >= 2 * edge_height`。

如果输入不满足约定，会抛出 `InputDataError`。

### 2. 边缘截取

算法从输入图中截取两个区域：

- 上边缘：`image[0:edge_height, :]`
- 下边缘：`image[-edge_height:, :]`

Rule 6_1 关心的是小图上下循环拼接时纹理是否连续，因此只分析上下边缘区域，不扫描整张图片。

### 3. 二值化

算法使用固定阈值进行反向二值化：

```python
_, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY_INV)
```

效果是：

- 深色纹理变为白色前景。
- 浅色背景变为黑色背景。

这样后续可以通过轮廓检测找到边缘纹理段。

### 4. 端点提取

当前公开入口使用 OpenCV 轮廓方式提取端点：

```python
top_ends = _extract_ends_from_contours(top_region, config)
bottom_ends = _extract_ends_from_contours(bottom_region, config)
```

每个端点的内部表示为：

```python
(min_x, max_x, line_type)
```

其中：

- 细线：`min_x == max_x`，表示中心点。
- 粗线：`min_x` 到 `max_x` 表示水平覆盖区间。
- `line_type` 为 `'fine'` 或 `'coarse'`。

宽度小于 `min_line_width` 的轮廓会被视为噪声并过滤。`min_line_width` 是算法内部参数，默认值为 `1`。

### 5. 端点匹配

算法使用上边缘端点和下边缘端点做匹配。

匹配规则如下：

| 组合 | 匹配条件 |
| --- | --- |
| 细线 - 细线 | 两个中心点水平距离不超过 `fine_match_distance`。 |
| 细线 - 粗线 | 细线中心点落在粗线区间内。 |
| 粗线 - 细线 | 细线中心点落在粗线区间内。 |
| 粗线 - 粗线 | 两个粗线区间存在水平重叠。 |

底边缘端点只会被匹配一次。如果多个上边缘端点都能匹配同一个下边缘端点，算法会按遍历顺序使用第一个匹配。

### 6. 连续性判定

最终判定规则：

```python
is_continuous = len(unmatched_bottom) == 0
```

也就是说，只要所有下边缘端点都能在上边缘找到匹配，就认为上下边缘连续。

如果上边缘存在额外端点，但下边缘端点都已匹配，仍判定为连续。这与旧系统行为一致：Rule 6_1 的核心风险是下边缘图案无法延续到上边缘。

### 7. Debug 可视化

当 `is_debug=True` 时，函数额外返回可视化图：

```python
is_continuous, vis_name, vis_image = detect_pattern_continuity(
	image,
	is_debug=True,
)
```

返回内容：

- `vis_name == "pattern_continuity.png"`
- `vis_image` 为 RGB 图像数组

可视化图中：

- 端点会被标记在上下边缘。
- 匹配端点之间会绘制连线。
- 未匹配端点会用高亮颜色标记。
- 边缘采样区域会用横线标出。

算法层不保存 `vis_image`。如果调用方需要保存，应在上层自行调用 `cv2.imwrite()`。

## 参数调节建议

### `threshold`

当纹理较浅或背景较暗时，阈值会直接影响前景提取。

- 阈值调大：更多像素会被当作深色纹理。
- 阈值调小：只有更暗的像素会被当作纹理。

默认值 `200` 来自旧系统配置，适用于当前测试数据中的灰度小图。

### `edge_height`

`edge_height` 决定上下边缘采样范围。

- 较小值：更贴近图片边界，抗干扰能力弱一些。
- 较大值：包含更多边缘附近纹理，但也可能引入非边界纹理。

图片高度必须满足：

```text
height >= 2 * edge_height
```

### `coarse_threshold`

`coarse_threshold` 决定纹理段被视为细线还是粗线。

- 宽度小于该值：按细线处理，使用中心点匹配。
- 宽度大于等于该值：按粗线处理，使用区间重叠匹配。

### `fine_match_distance`

`fine_match_distance` 是细线中心点允许的水平偏移容差。

- 较小值：判定更严格，轻微错位也可能不连续。
- 较大值：判定更宽松，可能放过实际错位。

## 示例

### 示例 1：基础连续性检测

```python
is_continuous, _, _ = detect_pattern_continuity(image)

if not is_continuous:
	print("图案上下边缘不连续")
```

### 示例 2：调整阈值和匹配容差

```python
is_continuous, _, _ = detect_pattern_continuity(
	image,
	threshold=180,
	fine_match_distance=6,
)
```

适用于图片整体偏暗、细线边缘存在轻微水平偏移的情况。

### 示例 3：生成 debug 图但不在算法层保存

```python
is_continuous, vis_name, vis_image = detect_pattern_continuity(
	image,
	is_debug=True,
)

if vis_image is not None:
	cv2.imwrite(f".results/{vis_name}", vis_image)
```

保存路径由调用方决定。算法层只返回建议文件名和图像数组。

### 示例 4：批量处理图片

```python
from pathlib import Path

for image_path in Path("tests/datasets/test_pattern_continuity/center_inf").glob("*.png"):
	buf = np.fromfile(str(image_path), dtype=np.uint8)
	image = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
	is_continuous, _, _ = detect_pattern_continuity(image)
	print(image_path.name, is_continuous)
```

批量处理时，建议调用方负责图片读取、错误记录和结果聚合。算法函数只处理单张图。

## 异常

### `InputDataError`

输入数据不满足算法前置条件时抛出。

常见原因：

- `image is None`
- 输入是三通道 BGR/RGB 图，而不是二维灰度图
- 图片高度小于 `2 * edge_height`

### `RuntimeProcessError`

算法执行过程中出现内部失败时抛出。

常见位置：

- OpenCV 二值化失败
- 端点匹配失败
- debug 可视化生成失败

## 内部函数说明

以下函数是模块内部实现细节，不建议在规则层或 API 层直接调用。

### `_detect_with_method_b`

使用 OpenCV 轮廓检测提取上下边缘端点。公开入口当前使用该方法。

### `_extract_ends_from_contours`

从二值边缘区域中提取细线或粗线端点。

### `_match_ends`

根据线型组合匹配上下边缘端点，并返回匹配关系与未匹配索引。

### `_can_match`

判断单个上边缘端点和单个下边缘端点是否匹配。

### `_visualize_detection`

生成 debug 可视化图像。该函数只返回 `np.ndarray`，不保存文件。

### `_detect_with_method_a`

保留的像素扫描实现，用于白盒测试和对比验证。当前公开入口不使用该方法。

## 设计边界

该算法刻意保持较窄的职责边界：

- 输入只接受单张灰度图和少量影响检测结果的参数。
- 输出只包含连续性结论和可选 debug 图。
- 不返回内部端点明细，避免规则层依赖算法实现细节。
- 不产生评分，评分应由 `src.rules` 层完成。
- 不保存图片，文件路径和结果目录应由调用方管理。

这种设计可以让算法层稳定复用，同时减少与规则层、节点层和 API 层的耦合。
