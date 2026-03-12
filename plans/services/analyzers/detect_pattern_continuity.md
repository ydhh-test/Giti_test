# 图案连续性检测功能实现计划

## 功能概述

检测灰度图中上下边缘的线条是否连续对齐，为后续的上下循环拼接服务。

## 核心逻辑

### 连续性判定标准

上下边缘的所有线条端点都能找到配对，满足匹配条件：
- 如果所有端点都匹配成功，则为**连续**（返回评分10分）
- 如果有任何端点无法匹配，则为**不连续**（返回评分0分）

### 匹配规则

**重要理解**：
- 不是"同一条线"的上下部分匹配
- 而是"上边缘的线头"与"下边缘的线头"进行配对
- 允许一对多（上边缘的一个粗线可以匹配下边缘的多个端点）
- 不允许多对一（下边缘的一个端点只能被匹配一次）

#### 1. 细线-细线匹配
- 端点表示：`(center_x, center_x, 'fine')`
- 匹配条件：`|center_x1 - center_x2| ≤ 4`（可配置）
- 语义：两个细线端点的水平距离在容差范围内

#### 2. 细线-粗线匹配
- 端点表示：细线 `(center_x, center_x, 'fine')`，粗线 `(min_x, max_x, 'coarse')`
- 匹配条件：`min_x ≤ center_x ≤ max_x`
- 语义：细线端点在粗线的区间范围内

#### 3. 粗线-粗线匹配
- 端点表示：`(min_x1, max_x1, 'coarse')` 和 `(min_x2, max_x2, 'coarse')`
- 匹配条件：区间重合度 ≥ 2/3（可配置）
- 重合度计算：
  - 重合长度 = `min(max_x1, max_x2) - max(min_x1, min_x2)`
  - 较短区间长度 = `min(max_x1 - min_x1, max_x2 - min_x2)`
  - 重合比例 = 重合长度 / 较短区间长度

## 端点提取逻辑

### 边缘区域定义
- **上边缘区域**：图片顶部 4 像素（y=0 到 y=3）
- **下边缘区域**：图片底部 4 像素（y=124 到 y=127，假设图片高度128）

### 端点识别
1. **深色判定**：像素值 ≤ 阈值（默认200）为线条，>阈值为背景
2. **连通区域**：在边缘区域内识别独立的深色连通区域
3. **端点提取**：
   - 对上边缘：检查 y=0 行，识别深色连通区间的 x 范围
   - 对下边缘：检查 y=127 行，识别深色连通区间的 x 范围
   - 如果连通区域在边缘有不连续的深色像素（中间被背景隔开），则识别为多个端点
4. **粗细线判定**：
   - 如果端点宽度 ≥ 5 像素，则为粗线
   - 否则为细线
5. **噪音过滤**：过滤掉宽度 < 1 像素的噪音

### 两种实现方法

#### 方法A：纯像素操作
- 直接操作像素数组
- 简单高效，易于理解和调试
- 适用于规则清晰的花纹图像

#### 方法B：OpenCV轮廓检测
- 使用 `cv2.findContours` 检测轮廓
- 利用轮廓的边界框信息
- 能更精确地识别不规则形状的线条

## 匹配算法

### 全排列组合匹配
使用 `itertools.product` 遍历所有 (top_idx, bottom_idx) 组合：

```python
from itertools import product

# 初始化
unmatched_bottom = set(range(len(bottom_ends)))
matches = []

# 全排列循环
for top_idx, bottom_idx in product(range(len(top_ends)), range(len(bottom_ends))):
    if bottom_idx in unmatched_bottom:  # 下边缘只能匹配一次
        if can_match(top_ends[top_idx], bottom_ends[bottom_idx]):
            unmatched_bottom.remove(bottom_idx)
            matches.append((top_idx, bottom_idx))

# 判定
is_continuous = len(unmatched_bottom) == 0  # 上边缘允许重复匹配，不需要检查
```

### 算法特点
- **一对多**：上边缘端点可以匹配多个下边缘端点（粗线覆盖多个细线）
- **非多对一**：下边缘端点只能被匹配一次
- **贪心策略**：按遍历顺序优先匹配
- **无需全局最优**：按x递增排序通常能得到较好的结果

## 函数接口设计

### 主函数

```python
def detect_pattern_continuity(
    image: np.ndarray,
    conf: Dict[str, Any],
    *args,
    **kwargs
) -> Tuple[int, Dict[str, Any]]:
    """
    检测图案上下边缘的连续性

    Parameters:
    - image: 输入灰度图 (H, W)
    - conf: 配置字典，包含评分规则和参数
    - *args, **kwargs: 额外参数（method='A'或'B', visualize=True等）

    Returns:
    - score: 评分（连续返回conf['score']，不连续返回0）
    - details: 详细信息字典

    details 包含:
    {
        'is_continuous': bool,
        'top_ends': List[Tuple[int, int, str]],
        'bottom_ends': List[Tuple[int, int, str]],
        'matches': List[Tuple[int, int]],
        'unmatched_top': List[int],
        'unmatched_bottom': List[int],
        'visualization': Optional[np.ndarray]
    }
    """
```

### 配置字典示例

```python
conf = {
    'score': 10,                      # 评分
    'threshold': 200,                 # 固定灰度阈值
    'edge_height': 4,                 # 边缘区域高度
    'coarse_threshold': 5,            # 粗细线宽度阈值
    'fine_match_distance': 4,         # 细线匹配距离
    'coarse_overlap_ratio': 0.67,     # 粗线重合比例
    'use_adaptive_threshold': False,  # 是否使用自适应阈值
    'adaptive_method': 'otsu',        # 自适应方法：'otsu'或'adaptive'
    'min_line_width': 1,              # 最小线条宽度
    'connectivity': 4,                # 连通性：4或8
    'vis_line_width': 2,              # 可视化线条宽度
    'vis_font_scale': 0.5             # 可视化字体大小
}
```

## 自适应阈值

### 支持两种方法

#### 1. Otsu算法
使用OpenCV的全局Otsu阈值算法：
```python
threshold, _ = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
```

#### 2. 局部自适应
使用图片的中位数或平均值作为参考：
```python
threshold = np.median(image)  # 或 np.mean(image)
```

### 使用方式
- 在配置字典中设置 `use_adaptive_threshold: True`
- 选择 `adaptive_method: 'otsu'` 或 `'adaptive'`
- 否则使用固定阈值 `threshold`

## 可视化功能

### 可视化内容
1. **线条标记**：
   - 不同线条用不同颜色标记（HSV颜色轮）
   - 细线：画圆点
   - 粗线：画矩形框

2. **匹配连线**：
   - 成功匹配：绿色连线
   - 显示匹配对的连接关系

3. **未匹配端点**：
   - 用黄色高亮显示
   - 圆点或矩形框加粗

4. **边缘区域标记**：
   - 标记顶部和底部4像素区域

### 可视化输出
- 返回RGB彩色图片（details['visualization']）
- 可保存为图片文件用于调试

## 文件结构

```
configs/
└── rules_config.py  # 配置类 PatternContinuityConfig

writing/
└── services/
    └── analyzers/
        └── detect_pattern_continuity.py  # 主模块
```

## 核心功能模块

### 1. 配置类 (PatternContinuityConfig)
- 位置：`configs/rules_config.py`
- 功能：管理所有配置参数
- 方法：`from_dict()` 从配置字典创建对象

### 2. 主函数 (detect_pattern_continuity)
- 位置：`writing/services/analyzers/detect_pattern_continuity.py`
- 功能：主入口，协调各子模块
- 输入：image, conf, method, visualize
- 输出：score, details

### 3. 端点提取
- `_detect_with_method_a()`: 纯像素操作
- `_detect_with_method_b()`: OpenCV轮廓检测
- `_extract_ends_from_region()`: 从边缘区域提取端点（方法A）
- `_extract_ends_from_contours()`: 从轮廓提取端点（方法B）

### 4. 匹配算法
- `_match_ends()`: 全排列匹配
- `_can_match()`: 判断两个端点是否可以匹配

### 5. 自适应阈值
- `get_adaptive_threshold()`: 计算自适应阈值

### 6. 可视化
- `_visualize_detection()`: 生成可视化图片
- `_generate_colors()`: 生成不同颜色

## 默认参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| score | 10 | 连续时的评分 |
| threshold | 200 | 固定灰度阈值 |
| edge_height | 4 | 边缘区域高度（像素） |
| coarse_threshold | 5 | 粗细线宽度阈值（像素） |
| fine_match_distance | 4 | 细线匹配的最大距离（像素） |
| coarse_overlap_ratio | 2/3 | 粗线匹配的最小重合比例 |
| use_adaptive_threshold | False | 是否使用自适应阈值 |
| adaptive_method | 'otsu' | 自适应方法 |
| min_line_width | 1 | 最小线条宽度（过滤噪音） |
| connectivity | 4 | 连通性判定（4或8） |
| vis_line_width | 2 | 可视化线条宽度 |
| vis_font_scale | 0.5 | 可视化字体大小 |

## 使用示例

```python
import numpy as np
import cv2
from writing.services.analyzers.detect_pattern_continuity import detect_pattern_continuity

# 读取图片
image = cv2.imread('pattern.png', cv2.IMREAD_GRAYSCALE)

# 配置字典
conf = {
    'score': 10,
    'threshold': 200,
    'edge_height': 4,
    'coarse_threshold': 5,
    'fine_match_distance': 4,
    'coarse_overlap_ratio': 0.67,
    'use_adaptive_threshold': False,
    'adaptive_method': 'otsu',
    'min_line_width': 1,
    'connectivity': 4,
    'vis_line_width': 2,
    'vis_font_scale': 0.5
}

# 调用函数（方法A，带可视化）
score, details = detect_pattern_continuity(
    image,
    conf,
    method='A',
    visualize=True
)

# 输出结果
print(f"Score: {score}")
print(f"Is continuous: {details['is_continuous']}")
print(f"Top ends: {details['top_ends']}")
print(f"Bottom ends: {details['bottom_ends']}")
print(f"Matches: {details['matches']}")
print(f"Unmatched top: {details['unmatched_top']}")
print(f"Unmatched bottom: {details['unmatched_bottom']}")

# 保存可视化结果
if details['visualization'] is not None:
    cv2.imwrite('visualization.png', details['visualization'])

# 对比方法A和方法B
score_a, details_a = detect_pattern_continuity(image, conf, method='A', visualize=False)
score_b, details_b = detect_pattern_continuity(image, conf, method='B', visualize=False)

print(f"Method A: {details_a['is_continuous']}")
print(f"Method B: {details_b['is_continuous']}")
```

## 边界情况处理

### 1. 空边缘
- 上边缘和下边缘都没有线条
- 判定为**连续**（没有线条需要匹配）

### 2. 一侧空边缘
- 只有上边缘或下边缘有线条
- 判定为**不连续**（有线条无法匹配）

### 3. 端点数量不匹配
- 上边缘3个端点，下边缘2个端点
- 即使2个端点匹配成功，仍有1个上端点无法匹配
- 判定为**不连续**

### 4. 斜线情况
- 斜线的上下端点x位置可能差异很大
- 这种情况下端点不应该匹配
- 如果有其他线条能配对，则连续；否则不连续

### 5. 粗线覆盖多细线
- 上边缘粗线[10, 60]，下边缘细线15, 25, 55
- 粗线可以匹配所有3个细线（一对多）
- 判定为**连续**

## 设计原则

1. **完全可配置**：所有参数都可通过配置字典调整
2. **两种实现方法**：支持方法A和方法B，可对比效果
3. **灵活的匹配算法**：支持一对多，适应粗线覆盖多细线的情况
4. **丰富的可视化**：便于调试和理解算法行为
5. **自适应阈值**：支持固定阈值和自适应阈值
6. **类型安全**：使用类型提示，便于IDE自动补全
7. **可扩展性**：通过 *args 和 **kwargs 保留扩展性

## 测试策略

1. **功能测试**：
   - 连续的图案（完美匹配）
   - 不连续的图案（线条错位）
   - 边界情况（空边缘、数量不匹配等）

2. **对比测试**：
   - 方法A和方法B的结果对比
   - 固定阈值和自适应阈值对比

3. **可视化验证**：
   - 人工检查可视化图片
   - 确认线条检测和匹配是否正确
   - 根据可视化结果调整参数

4. **性能测试**：
   - 测试在128x128图片上的运行时间
   - 确保实时性要求

## 后续优化方向

1. **多尺度检测**：对不同宽度的线条使用不同的检测策略
2. **线条角度信息**：如果边缘区域增大，可以考虑线条角度
3. **机器学习方法**：对于复杂花纹，可以考虑训练分类器
4. **并行处理**：同时运行方法A和方法B，交叉验证结果
5. **参数自动调优**：基于可视化结果自动调整参数
