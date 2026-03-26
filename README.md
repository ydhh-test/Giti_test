# 轮胎AI模式识别项目

基于深度学习的轮胎花纹识别与质量分析系统，提供从图像预处理、模式识别到质量评分的完整解决方案。

## 项目简介

本项目是针对轮胎制造行业的AI视觉检测解决方案，主要用于：
- 轮胎花纹图像的自动识别与分析
- 轮胎质量自动化评分
- 生产过程质量监控
- 轮胎花纹连续性检测

### 核心功能

- **图像预处理**：灰边去除、CMYK颜色空间转换
- **模式识别**：基于深度学习的花纹块生成
- **连续性检测**：图案上下边缘连续性分析
- **智能拼接**：纵图/横图自动拼接
- **规则引擎**：配置驱动的业务规则判定
- **后处理 9 阶段流程**：Conf 处理→小图筛选→小图打分→纵图拼接→横图拼接→横图打分→装饰边框→统计总分→整理输出
- **质量评分**：业务评分 + 美感评分
- **可视化输出**：检测结果可视化展示

## 快速开始

### 环境要求

- Python 3.12+
- 操作系统：Linux/macOS/Windows
- 内存：建议8GB以上

### 安装步骤

1. **克隆仓库**
```bash
git clone <repository-url>
cd giti-tire-ai-pattern
```

2. **创建虚拟环境**
```bash
python3.12 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **验证安装**
```bash
python -c "import cv2; import numpy; import PIL; print('依赖安装成功')"
pytest tests/ -v  # 运行测试
```

## 项目结构

```
giti-tire-ai-pattern/
├── configs/                 # 配置模块
│   ├── __init__.py
│   ├── base_config.py      # 基础配置
│   ├── complete_config.py  # 完整配置
│   ├── module_config.py    # 模块配置
│   ├── postprocessor_config.py  # 后处理配置
│   ├── rules_config.py     # 规则配置
│   └── user_config.py      # 用户配置
├── services/               # 核心服务模块（服务层）
│   ├── __init__.py
│   ├── analyzers.py        # 分析器服务
│   ├── inference.py        # 推理服务
│   ├── postprocessor.py    # 后处理服务
│   ├── preprocessor.py     # 预处理服务
│   └── scorer.py           # 评分服务
├── rules/                  # 规则层
│   ├── __init__.py
│   ├── rule1to5.py
│   ├── rule6_1.py
│   ├── rule6_2.py
│   ├── rule8_14.py         # 规则 8 & 14
│   ├── rule13.py
│   └── rule19.py
├── algorithms/             # 算法实现层
│   ├── __init__.py
│   ├── detection/          # 检测算法
│   │   ├── __init__.py
│   │   ├── pattern_continuity.py  # 连续性检测算法
│   │   └── groove_intersection.py # 横沟检测算法
│   └── stitching/          # 拼接算法
│       ├── __init__.py
│       ├── horizontal_stitch.py   # 横图拼接算法
│       └── vertical_stitch.py     # 纵图拼接算法
├── utils/                  # 工具模块
│   ├── __init__.py
│   ├── cv_utils.py        # 图像处理工具
│   ├── exceptions.py      # 异常处理
│   ├── io_utils.py        # I/O工具
│   └── logger.py          # 日志系统
├── tests/                  # 测试模块
│   ├── datasets/          # 测试数据集
│   └── unittests/         # 单元测试
│       ├── algorithms/    # 算法测试
│       └── services/      # 服务测试
├── docs/                   # 文档
│   ├── before_jobs/       # 前期工作文档
│   └── development/       # 开发文档
├── plans/                  # 计划文档（存储大模型生成的执行计划）
│   ├── merge_by_hand/     # 手动合并的计划
│   ├── rules/             # 规则相关计划
│   ├── scripts/           # 脚本相关计划
│   └── services/          # 服务相关计划
├── scripts/                # 脚本工具
│   ├── pieces_2_standard_input.py  # 准备输入数据脚本
│   ├── postprocessor.py            # 后处理运行脚本
│   └── small_image_filter.py       # 小图筛选脚本
├── tools/                  # 工具脚本
│   └── fetch-pr.sh         # PR 获取工具
├── ARCHITECTURE.md         # 架构设计文档
├── CONTRIBUTING.md         # 贡献指南
├── README.md              # 项目说明
└── requirements.txt        # 依赖列表
```

### 架构分层

项目采用分层架构设计：

- **服务层** (`services/`): 对外提供的服务接口，负责业务流程编排（预处理、推理、后处理、评分）
- **规则层** (`rules/`): 业务规则实现，配置驱动的规则判定
- **算法层** (`algorithms/`): 核心算法实现，按功能语义分组
  - `detection/`: 检测类算法（如连续性检测）
  - `stitching/`: 拼接类算法（如纵图拼接、横图拼接）
- **工具层** (`utils/`): 通用工具函数（日志、异常、图像处理、IO）
- **配置层** (`configs/`): 配置管理

**注意**: 用户代码应通过服务层接口调用，规则层和算法层为内部实现。

### 后处理 9 阶段流程

后处理模块实现完整的 9 阶段处理流程：

```
Conf 处理 → 小图筛选 → 小图打分 → 纵图拼接 → 横图拼接 → 横图打分 → 装饰边框 → 统计总分 → 整理输出
```

详细 API 说明请参考 [docs/api_postprocessor.md](docs/api_postprocessor.md)

## 使用指南

### 基本使用

```python
from services.preprocessor import preprocessor
from services.inference import inference
from services.postprocessor import postprocessor
from services.scorer import scorer

# 1. 图像预处理
task_id = "task_example_001"
conf = {...}  # 配置参数
user_conf = {...}  # 用户配置

# 预处理
preprocessor_result = preprocessor(task_id, conf, user_conf)

# 2. 推理识别
inference_result = inference(task_id, conf, user_conf)

# 3. 后处理
postprocessor_result = postprocessor(task_id, conf, user_conf)

# 4. 评分
score_result = scorer(task_id, conf, user_conf)
```

### 连续性检测示例

```python
from algorithms.detection.pattern_continuity import detect_pattern_continuity
import cv2
import numpy as np

# 读取图像
image = cv2.imread("tire_pattern.png", cv2.IMREAD_GRAYSCALE)

# 配置参数
conf = {
    'score': 10,
    'threshold': 200,
    'edge_height': 4,
    'coarse_threshold': 5,
    'fine_match_distance': 4
}

# 执行检测
score, details = detect_pattern_continuity(
    image=image,
    conf=conf,
    method='B',  # 使用OpenCV轮廓检测
    visualize=True,
    task_id='task_example_001',
    image_type='center_inf',
    image_id='0'
)

print(f"连续性评分: {score}")
print(f"详细信息: {details}")
```

### 配置管理

配置文件位于 `configs/` 目录，支持：
- 基础系统配置 (`base_config.py`)
- 业务规则配置 (`rules_config.py`)
- 后处理参数配置 (`postprocessor_config.py`)

#### 配置规范

**核心原则：配置文件中不应该出现任何带 "test" 的路径。**

- 所有配置路径指向 `.results/` 目录（项目根目录的子目录）
- 测试数据由测试准备函数从 `tests/datasets/` 拷贝到 `.results/`
- 功能函数对 `.results/` 目录进行操作，不直接操作 `tests/datasets/`
- 使用 `Path` 进行路径拼接，确保跨平台兼容（Windows/Linux/macOS）

详细规范请参考 [.claude/skills/config-and-test-data-management.md](.claude/skills/config-and-test-data-management.md)

## 开发指南

### 代码规范

- 遵循 PEP 8 编码规范
- 使用类型注解 (Type Hints)
- 编写文档字符串 (Docstrings)
- 使用中文注释和文档

### 测试要求

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/unittests/algorithms/detection/test_pattern_continuity.py -v

# 生成覆盖率报告
pytest tests/ --cov=services --cov=utils --cov-report=html
```

### 日志系统

```python
from utils.logger import get_logger

logger = get_logger("module_name")
logger.info("信息日志")
logger.warning("警告日志")
logger.error("错误日志")
```

### 异常处理

```python
from utils.exceptions import (
    ImageProcessingError,
    PatternDetectionError,
    ConfigurationError
)

try:
    # 业务逻辑
    pass
except ImageProcessingError as e:
    logger.error(f"图像处理错误: {e}")
except PatternDetectionError as e:
    logger.error(f"图案检测错误: {e}")
```

## 部署说明

详细的部署指南请参考 [docs/deployment.md](docs/deployment.md)

### 快速运行

```bash
# 1. 环境配置
python3.12 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行测试（可选）
pytest tests/unittests/services/test_preprocessor.py -v

# 4. 准备输入数据
python scripts/pieces_2_standard_input.py --task_id <TASK_ID>

# 5. 运行后处理
python scripts/postprocessor.py --task-id <TASK_ID>
```

## 架构设计

详细的架构设计文档请参考 [ARCHITECTURE.md](ARCHITECTURE.md)

### 系统架构

```
┌─────────────────────────────────────────┐
│         服务层 (Service)                │
│  Preprocessor | Inference | Postproc   │
│  Scorer                                 │
├─────────────────────────────────────────┤
│         规则层 (Rules)                  │
│  rule1to5 | rule6_1 | rule6_2 | rule8_14 | ... │
├─────────────────────────────────────────┤
│         算法层 (Algorithms)             │
│  detection/     |    stitching/         │
│  (连续性/横沟检测) | (纵图/横图拼接)    │
├─────────────────────────────────────────┤
│         工具层 (Utility)                │
│  Logger | Exceptions | CV Utils | IO   │
├─────────────────────────────────────────┤
│         配置层 (Config)                 │
│  base | module | postprocessor | rules │
└─────────────────────────────────────────┘
```

## 性能指标

- **图像处理速度**：单张图片 < 100ms
- **测试覆盖**：当前 16 个测试文件，192 个测试方法

## 贡献指南

详细的贡献指南请参考 [CONTRIBUTING.md](CONTRIBUTING.md)

### 贡献流程

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循现有代码风格
- 编写单元测试
- 更新相关文档
- 通过所有测试检查

## 常见问题

### Q: 如何处理CMYK格式的图像？
A: 系统会自动检测并转换CMYK到RGB格式，无需手动处理。

### Q: 支持哪些图像格式？
A: 支持常见格式：JPG, PNG, TIFF, BMP等。

### Q: 如何调整连续性检测的灵敏度？
A: 修改 `configs/rules_config.py` 中的 `PatternContinuityConfig` 参数。

### Q: 系统对硬件有什么要求？
A: 最低配置：4核CPU，8GB内存。推荐配置：8核CPU，16GB内存，GPU支持。

## 版本历史

### v2.1.0 (2026-03-26)
- **规则引擎**：新增横沟检测规则（rule8_14.py），支持规则 8 & 14
- **算法层**：新增横沟检测算法（groove_intersection.py）
- **评分模块**：新增陆海比评分算法（land_sea_ratio.py）
- **测试体系**：新增横沟检测相关测试，测试数量提升至 192 个测试方法
- **工具脚本**：新增 fetch-pr.sh 工具

### v2.0.0 MVP (2026-03-12)
- **后处理模块**：实现完整 9 阶段处理流程（Conf 处理→小图筛选→小图打分→纵图拼接→横图拼接→横图打分→装饰边框→统计总分→整理输出）
- **规则引擎**：新增 5 个规则文件（rule1to5、rule6_1、rule6_2、rule13、rule19）
- **算法层**：新增横图拼接算法（horizontal_stitch.py）
- **测试体系**：新增单元测试 + 集成测试，覆盖核心功能
- **配置系统**：完善 6 个配置文件，支持配置驱动
- **脚本工具**：新增 3 个脚本（pieces_2_standard_input.py、postprocessor.py、small_image_filter.py）

### v1.0.0 (2026-03-08)
- 完成基础架构设计
- 实现核心模块：预处理、推理、后处理、评分
- 完成连续性检测功能
- 实现异常处理和日志系统
- 26个单元测试全部通过
- 完善依赖管理和配置系统

## 技术栈

- **编程语言**：Python 3.12
- **图像处理**：OpenCV, Pillow
- **数据处理**：NumPy, Pandas
- **可视化**：Matplotlib
- **测试框架**：Pytest
- **版本控制**：Git


## 许可证

Copyright © 2026. All rights reserved.

---

**注意**：本项目主要用于对内测试VibeCoding范式协作方法，不作为最终交付代码仓库使用。项目包含JT轮胎后处理部分，内容详见飞书文档。

**警告**：请不要向main分支提merge。
