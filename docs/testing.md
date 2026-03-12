# 测试指南

## 测试目录结构

```
tests/
├── datasets/                    # 测试数据集
│   ├── detect_pattern_continuity/
│   │   ├── center_inf/          # 中心区域测试图片
│   │   └── side_inf/            # 边缘区域测试图片
│   ├── side_filter/             # 小图筛选测试数据
│   ├── side_inf/                # 边缘区域测试数据
│   └── task_integration/        # 集成测试数据
│       ├── task_id_test_rule13/
│       └── task_id_test_rule1to5/
├── integration/                 # 集成测试
│   └── services/
│       ├── __init__.py
│       ├── test_postprocessor_pipeline.py   # 后处理流水线测试
│       └── test_postprocessor_stages.py     # 后处理阶段测试
└── unittests/                   # 单元测试
    ├── __init__.py
    ├── algorithms/              # 算法测试
    │   ├── detection/
    │   │   └── test_pattern_continuity.py   # 连续性检测测试
    │   └── stitching/
    │       ├── test_horizontal_stitch.py    # 横图拼接测试
    │       └── test_vertical_stitch.py      # 纵图拼接测试
    ├── rules/                   # 规则测试
    │   ├── test_rule1to5.py
    │   ├── test_rule6_1.py
    │   ├── test_rule6_2.py
    │   └── test_rule13.py
    ├── rules/scoring/           # 规则评分测试
    │   └── test_land_sea_ratio.py
    ├── services/                # 服务测试
    │   ├── test_postprocessor.py
    │   └── test_preprocessor.py
    └── test_utils/              # 工具测试
        └── test_cv_utils.py
```

---

## 运行测试

### 环境准备

```bash
# 激活虚拟环境
source .setup_giti_speckit_py12.sh
```

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定测试

**预处理测试**
```bash
pytest tests/unittests/services/test_preprocessor.py -v
```

**后处理测试**
```bash
pytest tests/unittests/services/test_postprocessor.py -v
```

**算法测试**
```bash
# 连续性检测
pytest tests/unittests/algorithms/detection/test_pattern_continuity.py -v

# 纵图拼接
pytest tests/unittests/algorithms/stitching/test_vertical_stitch.py -v

# 横图拼接
pytest tests/unittests/algorithms/stitching/test_horizontal_stitch.py -v
```

**规则测试**
```bash
# 规则 1-5
pytest tests/unittests/rules/test_rule1to5.py -v

# 规则 6-1
pytest tests/unittests/rules/test_rule6_1.py -v

# 规则 6-2
pytest tests/unittests/rules/test_rule6_2.py -v

# 规则 13
pytest tests/unittests/rules/test_rule13.py -v
```

**集成测试**
```bash
# 后处理流水线
pytest tests/integration/services/test_postprocessor_pipeline.py -v

# 后处理阶段
pytest tests/integration/services/test_postprocessor_stages.py -v
```

### 生成覆盖率报告

```bash
# HTML 格式
pytest tests/ --cov=services --cov=algorithms --cov=rules --cov-report=html

# 终端格式
pytest tests/ --cov=services --cov=algorithms --cov=rules --cov-report=term-missing

# XML 格式（用于 CI/CD）
pytest tests/ --cov=services --cov=algorithms --cov=rules --cov-report=xml
```

---

## 测试数据管理

### 测试数据位置

测试数据位于 `tests/datasets/` 目录，按功能分类：

- `detect_pattern_continuity/` - 连续性检测测试数据
- `side_filter/` - 小图筛选测试数据
- `task_integration/` - 集成测试数据

### 测试数据使用规范

- 功能代码操作 `.results/` 目录，不直接操作 `tests/datasets/`
- 测试准备函数负责将数据从 `tests/datasets/` 拷贝到 `.results/`
- 测试完成后，清理 `.results/` 目录中的测试数据

---

## 测试用例说明

### 单元测试

单元测试针对单个函数或类进行测试：

| 测试文件 | 测试对象 | 测试内容 |
|----------|----------|----------|
| `test_pattern_continuity.py` | `detect_pattern_continuity` | 连续性检测算法 |
| `test_vertical_stitch.py` | `stitch_and_resize` | 纵图拼接功能 |
| `test_horizontal_stitch.py` | `horizontal_stitch` | 横图拼接功能 |
| `test_preprocessor.py` | `preprocessor` | 预处理服务 |
| `test_postprocessor.py` | `postprocessor` | 后处理服务 |
| `test_rule*.py` | 各规则函数 | 规则判定逻辑 |

### 集成测试

集成测试测试多个模块的协同工作：

| 测试文件 | 测试内容 |
|----------|----------|
| `test_postprocessor_pipeline.py` | 完整后处理流水线 |
| `test_postprocessor_stages.py` | 后处理各阶段 |

---

## 编写新测试

### 测试模板

```python
import pytest
from pathlib import Path

def test_feature_name():
    """测试说明"""
    # Arrange - 准备测试数据
    test_data = ...

    # Act - 执行被测函数
    result = function_to_test(test_data)

    # Assert - 验证结果
    assert result == expected_value
```

### 测试准备函数示例

```python
def prepare_test_data(task_id: str):
    """
    准备测试数据

    将测试数据从 tests/datasets/ 拷贝到 .results/
    """
    import shutil
    from pathlib import Path

    source = Path("tests/datasets") / task_id
    dest = Path(".results/tasks") / task_id

    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
```

### 测试清理函数示例

```python
def cleanup_test_data(task_id: str):
    """
    清理测试数据

    删除 .results/ 目录中的测试数据
    """
    import shutil
    from pathlib import Path

    dest = Path(".results/tasks") / task_id
    if dest.exists():
        shutil.rmtree(dest)
```

---

## 常见问题

### Q: 测试失败如何调试？
A: 使用 `-v` 参数查看详细输出，使用 `--tb=long` 查看完整堆栈跟踪。

### Q: 如何运行单个测试函数？
A: 使用 `-k` 参数过滤，如 `pytest tests/ -k test_pattern_continuity -v`

### Q: 测试数据在哪里下载？
A: 测试数据包含在仓库的 `tests/datasets/` 目录中。

### Q: 如何添加新的测试用例？
A: 在对应的测试文件中添加新的测试函数，遵循 `test_` 命名规范。

---

## 相关文件

- [部署指南](deployment.md) - 部署和运行说明
- [API 参考](api_postprocessor.md) - API 使用说明
