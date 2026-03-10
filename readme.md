# Giti Tire AI Pattern

轮胎花纹AI分析系统 - 海陆比计算与RIB拼接

## 项目简介

本项目是佳通轮胎（Giti Tire）后处理AI系统，用于分析轮胎花纹设计的几何合理性。主要功能包括：

- **海陆比计算**：分析轮胎花纹中深沟槽和浅沟槽的占比
- **RIB拼接**：将多个RIB（胎面花纹块）进行拼接，生成完整花纹
- **评分系统**：根据海陆比标准对花纹进行评分

## 技术栈

- Python 3.8+
- OpenCV (图像处理)
- NumPy (数值计算)
- pytest (单元测试)

## 项目结构

```
giti-tire-ai-pattern/
├── configs/                 # 配置模块
│   ├── postprocessor_config.py  # 后处理配置
│   └── ...                  # 其他配置
├── services/               # 核心服务模块
│   ├── analyzers.py        # 海陆比分析
│   ├── postprocessor.py    # RIB拼接
│   └── preprocessor.py     # 预处理
├── tests/                  # 测试模块
│   ├── datasets/           # 测试数据
│   │   ├── split/          # RIB拼接测试数据
│   │   │   ├── center/     # 中间RIB图片
│   │   │   └── side-de-gray/  # 边缘RIB图片
│   │   ├── test_data_land_sea/  # 海陆比测试数据
│   │   └── test_data_land_sea_visual/  # 可视化测试结果
│   └── unittests/          # 单元测试
│       └── services/
│           ├── test_analyzers.py    # 海陆比分析测试
│           └── test_postprocessor.py # RIB拼接测试
├── .results/               # 结果目录
│   ├── data/               # 生成数据
│   │   └── whole_img/      # 完整花纹图片
│   └── split/              # 分割结果
├── readme.md               # 项目说明
└── requirements.txt        # 依赖列表
```

## 安装

1. 克隆项目
2. 安装依赖：

```bash
pip install -r requirements.txt
```

或使用 conda 环境：

```bash
conda env create -f environment.yml
conda activate b-deal
```

## 使用方法

### 运行主程序

```bash
python services/postprocessor.py
```

### 海陆比计算示例

```python
import cv2
import numpy as np
from services.analyzers import compute_land_sea_ratio

# 配置参数
config = {
    "target_min": 28.0,
    "target_max": 35.0,
    "margin": 5.0
}

# 读取图片
img = cv2.imdecode(np.fromfile("test.png", dtype=np.uint8), cv2.IMREAD_COLOR)

# 计算海陆比
score, details = compute_land_sea_ratio(img, config)

print(f"海陆比: {details['ratio_value']}%")
print(f"评分: {score} 分")
```

### RIB拼接示例

```python
from services.postprocessor import generate_layout_images, load_images_from_directories

# 加载图片
center_images, side_images, image_names = load_images_from_directories()

# 生成布局图 (5 RIB, 非对称模式)
results = generate_layout_images(
    center_images, 
    side_images, 
    rib_count=5, 
    symmetry_type="asymmetric"
)

# 保存结果
save_results(results)
```

## 配置说明

### 海陆比评分规则

| 参数 | 说明 | 默认值 |
|-----|------|-------|
| target_min | 目标最小值(%) | 28.0 |
| target_max | 目标最大值(%) | 35.0 |
| margin | 容差范围 | 5.0 |

### 评分标准

| 分数 | 等级 | 说明 |
|-----|------|------|
| 2 | 优秀 | 海陆比在目标区间 [28%, 35%] 内 |
| 1 | 及格 | 海陆比在容差范围内 |
| 0 | 不合格 | 海陆比超出容差范围 |

### 像素阈值

| 区域 | 灰度范围 | 说明 |
|-----|---------|------|
| 黑色 | 0-50 | 深沟槽 |
| 灰色 | 51-200 | 浅沟槽/细花 |
| 白色 | 201-255 | 胎面 |

### RIB拼接对称模式

| 模式 | 说明 |
|-----|------|
| asymmetric | 非对称模式 |
| rotate180 | 旋转180°对称 |
| mirror | 镜像对称 |
| mirror_shifted | 镜像错位对称 |
| random | 随机选择一种模式 |

## 开发指南

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/unittests/services/test_postprocessor.py -v
pytest tests/unittests/services/test_analyzers.py -v

# 使用 conda 环境运行
conda run -n b-deal python -m pytest tests/ -v
```

### 测试说明

项目包含以下单元测试：

1. **test_analyzers.py** - 海陆比分析测试
   - 黑色/灰色区域计算
   - 海陆比评分逻辑
   - 真实图片集成测试

2. **test_postprocessor.py** - RIB拼接测试
   - 核心函数 `assemble_symmetry_layout` 测试
   - `CombinationManager` 组合管理测试
   - 辅助函数测试
   - 对称模式测试 (rotate180, mirror, mirror_shifted)
   - 真实数据集成测试

### 测试数据

- `tests/datasets/split/` - RIB拼接测试数据
  - `center/` - 中间RIB图片 (12张)
  - `side-de-gray/` - 边缘RIB图片 (8张)
- `tests/datasets/test_data_land_sea/` - 海陆比测试数据

### 添加新功能

1. 在 `services/` 目录下创建或修改服务模块
2. 在 `tests/unittests/services/` 下添加对应的单元测试
3. 更新 `configs/` 中的相关配置

## 输出结果

运行后，结果将保存在以下目录：

- `.results/data/whole_img/` - 完整花纹图片
- `.results/split/` - 分割结果
- `.logs/` - 日志文件

## 许可证

内部项目

## 联系方式

技术支持：佳通轮胎AI团队
