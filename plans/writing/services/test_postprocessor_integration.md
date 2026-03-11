# services/postprocessor.py 集成测试计划

**创建日期**: 2026-03-11
**测试数据**: `tests/datasets/task_integration/`

---

## 一、测试目标

为 `services/postprocessor.py` 模块设计完整的集成测试，覆盖后处理 9 个阶段的独立测试和全流程端到端测试。

---

## 二、测试数据说明

### 2.1 测试数据位置

```
tests/datasets/task_integration/
├── center_inf/
│   ├── 0.png
│   ├── 2.png
│   └── 4.png
└── side_inf/
    ├── 1.png
    └── 3.png
```

### 2.2 测试数据说明

| 目录 | 图片数量 | 说明 |
|------|----------|------|
| center_inf | 3 张 | 中心花纹原始图片 |
| side_inf | 2 张 | 侧花原始图片 |

---

## 三、后处理 9 个阶段概览

| 阶段 | 函数 | 依赖模块 | 实现状态 |
|------|------|----------|----------|
| 1. Conf 处理 | `_load_user_conf`, `_merge_conf_from_complete_config` | CompleteConfig | 已实现 |
| 2. 小图筛选 | `_small_image_filter` | rules/rule6_1 | 已实现 |
| 3. 小图打分 | `_small_image_score` | - | TODO |
| 4. 纵图拼接 | `_vertical_stitch` | rules/rule6_2 | 已实现 |
| 5. 横图拼接 | `_horizontal_stitch` | rules/rule1to5 | 已实现 |
| 6. 横图打分 | `_horizontal_image_score` | rules/rule13 | 已实现 |
| 7. 装饰边框 | `_add_decoration_borders` | rules/rule19 | 已实现 |
| 8. 统计总分 | `_calculate_total_score` | - | TODO |
| 9. 整理输出 | `_standard_input` | - | TODO |

---

## 四、测试代码结构

### 4.1 文件组织

```
tests/
├── integration/
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── test_postprocessor_stages.py      # 各阶段独立集成测试
│       └── test_postprocessor_pipeline.py    # 全流程端到端集成测试
```

### 4.2 文件内容划分

#### `test_postprocessor_stages.py`
- `TestStage12Integration` - Conf 处理 + 小图筛选
- `TestStage4Integration` - 纵图拼接
- `TestStage5Integration` - 横图拼接
- `TestStage67Integration` - 横图打分 + 装饰边框
- `TestExceptionScenarios` - 异常场景测试

#### `test_postprocessor_pipeline.py`
- `TestFullPipelineIntegration` - 完整 9 阶段流程测试
- `TestFullPipelineEdgeCases` - 边界情况测试

---

## 五、测试用例详细设计

### 5.1 工具函数

```python
def prepare_task_integration_data(task_id: str) -> Path:
    """
    准备 task_integration 测试数据

    将 tests/datasets/task_integration 下的数据拷贝到 .results/task_id_{task_id}/
    """

def cleanup_task_data(task_id: str):
    """清理任务测试数据"""
```

---

### 5.2 TestStage12Integration (Stage 1-2: Conf + 小图筛选)

**测试类**: `TestStage12Integration`
**测试文件**: `test_postprocessor_stages.py`

| 测试用例 | 测试内容 | 预期结果 |
|----------|----------|----------|
| `test_conf_processing_with_dict` | Conf 处理 - dict 输入 | 正确加载并合并配置 |
| `test_conf_processing_with_json_file` | Conf 处理 - JSON 文件输入 | 正确读取 JSON 文件 |
| `test_small_image_filter_integration` | 小图筛选完整流程 | 生成 filter 目录，返回正确统计 |

**前置准备**:
- 复制 `center_inf` 和 `side_inf` 到 `.results/task_id_{task_id}/`

**验证点**:
- filter 目录生成 (`center_filter`, `side_filter`)
- 返回格式包含 `image_gen_number`, `pattern_continuity_stats`

---

### 5.3 TestStage4Integration (Stage 4: 纵图拼接)

**测试类**: `TestStage4Integration`
**测试文件**: `test_postprocessor_stages.py`

| 测试用例 | 测试内容 | 预期结果 |
|----------|----------|----------|
| `test_vertical_stitch_integration` | 纵图拼接完整流程 | 生成 vertical 目录，返回正确统计 |
| `test_vertical_stitch_missing_config` | 纵图拼接 - 配置缺失 | 返回错误，err_msg 包含缺失字段 |

**前置准备**:
- 先执行小图筛选，生成 `center_filter` 和 `side_filter` 目录

**验证点**:
- 输出目录生成 (`center_vertical`, `side_vertical`)
- 返回格式包含 `directories`, `summary`

---

### 5.4 TestStage5Integration (Stage 5: 横图拼接)

**测试类**: `TestStage5Integration`
**测试文件**: `test_postprocessor_stages.py`

| 测试用例 | 测试内容 | 预期结果 |
|----------|----------|----------|
| `test_horizontal_stitch_integration` | 横图拼接完整流程 | 生成 combine_horizontal 目录 |

**前置准备**:
- 先执行小图筛选 → 纵图拼接

**验证点**:
- 输出目录生成 (`combine_horizontal`)
- 返回格式包含 `directories`, `summary`

---

### 5.5 TestStage67Integration (Stage 6-7: 横图打分 + 装饰边框)

**测试类**: `TestStage67Integration`
**测试文件**: `test_postprocessor_stages.py`

| 测试用例 | 测试内容 | 预期结果 |
|----------|----------|----------|
| `test_horizontal_image_score_integration` | 横图打分完整流程 | 返回评分统计 |
| `test_add_decoration_borders_integration` | 装饰边框完整流程 | 生成 combine 目录 |

**前置准备**:
- 先执行小图筛选 → 纵图拼接 → 横图拼接

**验证点**:
- 装饰边框输出目录生成 (`combine`)
- 返回格式包含 `image_gen_number`, `decoration_style`

---

### 5.6 TestFullPipelineIntegration (全流程端到端)

**测试类**: `TestFullPipelineIntegration`
**测试文件**: `test_postprocessor_pipeline.py`

| 测试用例 | 测试内容 | 预期结果 |
|----------|----------|----------|
| `test_full_pipeline_with_mock_todos` | 全流程 - Mock TODO 阶段 | 全流程成功完成 |
| `test_full_pipeline_empty_config` | 全流程 - 空配置 | 能够处理空配置 |

**Mock 处理**:
- `_small_image_score` → 返回 `(True, {"image_gen_number": 2})`
- `_calculate_total_score` → 返回 `(True, {"total_score": 85.0})`
- `_standard_input` → 返回 `(True, {"image_gen_number": 1})`

**验证点**:
- 最终返回 `flag=True`
- 返回格式包含 `image_gen_number`

---

### 5.7 TestExceptionScenarios (异常场景)

**测试类**: `TestExceptionScenarios`
**测试文件**: `test_postprocessor_stages.py`

| 测试用例 | 测试内容 | 预期结果 |
|----------|----------|----------|
| `test_invalid_user_conf_type` | 无效 user_conf 类型 | 返回错误，failed_stage=conf_processing |
| `test_json_file_not_found` | JSON 文件不存在 | 返回错误，failed_stage=conf_processing |
| `test_vertical_stitch_empty_config` | 纵图拼接空配置 | 返回错误 |
| `test_horizontal_stitch_empty_config` | 横图拼接空配置 | 返回错误 |
| `test_decoration_missing_input_dir` | 装饰边框输入目录不存在 | 返回空结果但不报错 |
| `test_stage_failure_propagation` | 阶段失败传播 | 错误正确传递，failed_stage 正确设置 |

---

## 六、TODO 阶段处理策略

| 阶段 | 函数 | 测试策略 |
|------|------|----------|
| Stage 3 | `_small_image_score` | 使用 `unittest.mock.patch` 模拟返回 |
| Stage 8 | `_calculate_total_score` | 使用 `unittest.mock.patch` 模拟返回 |
| Stage 9 | `_standard_input` | 使用 `unittest.mock.patch` 模拟返回 |

---

## 七、测试执行命令

```bash
# 运行所有集成测试
pytest tests/integration/services/test_postprocessor_stages.py -v
pytest tests/integration/services/test_postprocessor_pipeline.py -v

# 运行特定测试类
pytest tests/integration/services/test_postprocessor_stages.py::TestStage12Integration -v
pytest tests/integration/services/test_postprocessor_stages.py::TestStage4Integration -v
pytest tests/integration/services/test_postprocessor_stages.py::TestExceptionScenarios -v
pytest tests/integration/services/test_postprocessor_pipeline.py::TestFullPipelineIntegration -v

# 运行测试并生成覆盖率报告
pytest tests/integration/services/ --cov=services/postprocessor --cov-report=html
```

---

## 八、测试依赖

### 8.1 Python 依赖
- pytest
- unittest.mock (内置)

### 8.2 模块依赖
- `services/postprocessor.py`
- `rules/rule6_1.py` (pattern_continuity)
- `rules/rule6_2.py` (vertical_stitch)
- `rules/rule1to5.py` (horizontal_stitch)
- `rules/rule13.py` (horizontal_image_score)
- `rules/rule19.py` (decoration_borders)
- `configs/base_config.py` (SystemConfig)
- `configs/user_config.py` (DEFAULT_HORIZONTAL_STITCH_CONF, DEFAULT_VERTICAL_STITCH_CONF)

---

## 九、测试环境要求

- 测试前后需清理 `.results/` 目录
- 每个测试用例使用独立的 `task_id`
- 测试数据从 `tests/datasets/task_integration/` 复制

---

## 十、注意事项

1. **不要修改任何源代码** - 本计划仅用于测试设计
2. **测试数据不可变** - `tests/datasets/task_integration/` 下的图片不应被修改
3. **测试隔离** - 每个测试用例应独立运行，不依赖其他测试的状态
4. **Fixture 自动清理** - 使用 `@pytest.fixture(autouse=True)` 确保测试后清理

---

## 附录：完整测试代码模板

### A.1 `tests/integration/services/__init__.py`

```python
# -*- coding: utf-8 -*-
"""集成测试 services 模块"""
```

### A.2 `tests/integration/services/test_postprocessor_stages.py`

```python
# -*- coding: utf-8 -*-
"""
postprocessor 阶段集成测试

测试各阶段独立工作的正确性
"""

import pytest
import shutil
from pathlib import Path

from services.postprocessor import (
    postprocessor,
    _load_user_conf,
    _merge_conf_from_complete_config,
    _small_image_filter,
    _vertical_stitch,
    _horizontal_stitch,
    _horizontal_image_score,
    _add_decoration_borders,
)

# 项目根目录和测试数据目录
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_TEST_DATASETS_DIR = _PROJECT_ROOT / "tests" / "datasets" / "task_integration"
_RESULTS_DIR = _PROJECT_ROOT / ".results"


def prepare_task_integration_data(task_id: str) -> Path:
    """准备 task_integration 测试数据"""
    task_dir = _RESULTS_DIR / f"task_id_{task_id}"

    if task_dir.exists():
        shutil.rmtree(task_dir)

    task_dir.mkdir(parents=True, exist_ok=True)

    for inf_dir in ["center_inf", "side_inf"]:
        src = _TEST_DATASETS_DIR / inf_dir
        dst = task_dir / inf_dir
        if src.exists():
            shutil.copytree(src, dst)

    return task_dir


def cleanup_task_data(task_id: str):
    """清理任务测试数据"""
    task_dir = _RESULTS_DIR / f"task_id_{task_id}"
    if task_dir.exists():
        shutil.rmtree(task_dir)


class TestStage12Integration:
    """Stage 1-2 集成测试：Conf 处理 + 小图筛选"""

    TEST_TASK_ID = "test_stage12"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_conf_processing_with_dict(self):
        """测试 Conf 处理 - dict 输入"""
        user_conf = {"tire_design_width": 250}
        result = _load_user_conf(user_conf)
        assert result == user_conf

        merged = _merge_conf_from_complete_config(self.TEST_TASK_ID, user_conf)
        assert merged["tire_design_width"] == 250
        assert "vertical_stitch_conf" in merged

    def test_small_image_filter_integration(self):
        """测试小图筛选完整流程"""
        conf = {
            "filter_output_dirs": ["center_filter", "side_filter"],
            "pattern_continuity_conf": {
                "score": 10, "threshold": 200, "edge_height": 4,
                "coarse_threshold": 5, "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1, "connectivity": 4,
            },
            "visualize": True
        }

        flag, details = _small_image_filter(self.TEST_TASK_ID, conf)

        assert flag is True
        assert "image_gen_number" in details
        assert "pattern_continuity_stats" in details


class TestStage4Integration:
    """Stage 4 集成测试：纵图拼接"""

    TEST_TASK_ID = "test_stage4_vertical"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        from services.postprocessor import _small_image_filter
        _small_image_filter(self.TEST_TASK_ID, {
            "filter_output_dirs": ["center_filter", "side_filter"],
            "pattern_continuity_conf": {
                "score": 10, "threshold": 200, "edge_height": 4,
                "coarse_threshold": 5, "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1, "connectivity": 4,
            },
            "visualize": True
        })
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_vertical_stitch_integration(self):
        """测试纵图拼接完整流程"""
        conf = {
            "center_vertical": {"resolution": [1000, 2000]},
            "side_vertical": {"resolution": [1000, 2000]},
            "center_count": 3,
            "side_count": 2,
        }

        flag, details = _vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True
        assert "directories" in details

        task_dir = _RESULTS_DIR / f"task_id_{self.TEST_TASK_ID}"
        assert (task_dir / "center_vertical").exists()
        assert (task_dir / "side_vertical").exists()


class TestStage5Integration:
    """Stage 5 集成测试：横图拼接"""

    TEST_TASK_ID = "test_stage5_horizontal"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        from services.postprocessor import _small_image_filter, _vertical_stitch
        _small_image_filter(self.TEST_TASK_ID, {
            "filter_output_dirs": ["center_filter", "side_filter"],
            "pattern_continuity_conf": {
                "score": 10, "threshold": 200, "edge_height": 4,
                "coarse_threshold": 5, "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1, "connectivity": 4,
            },
            "visualize": True
        })
        _vertical_stitch(self.TEST_TASK_ID, {
            "center_vertical": {"resolution": [1000, 2000]},
            "side_vertical": {"resolution": [1000, 2000]},
            "center_count": 3,
            "side_count": 2,
        })
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_horizontal_stitch_integration(self):
        """测试横图拼接完整流程"""
        from configs.user_config import DEFAULT_HORIZONTAL_STITCH_CONF

        flag, details = _horizontal_stitch(self.TEST_TASK_ID, DEFAULT_HORIZONTAL_STITCH_CONF)

        assert flag is True
        assert "directories" in details

        task_dir = _RESULTS_DIR / f"task_id_{self.TEST_TASK_ID}"
        assert (task_dir / "combine_horizontal").exists()


class TestStage67Integration:
    """Stage 6-7 集成测试：横图打分 + 装饰边框"""

    TEST_TASK_ID = "test_stage67"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        from services.postprocessor import _small_image_filter, _vertical_stitch, _horizontal_stitch
        from configs.user_config import DEFAULT_HORIZONTAL_STITCH_CONF

        _small_image_filter(self.TEST_TASK_ID, {
            "filter_output_dirs": ["center_filter", "side_filter"],
            "pattern_continuity_conf": {
                "score": 10, "threshold": 200, "edge_height": 4,
                "coarse_threshold": 5, "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1, "connectivity": 4,
            },
            "visualize": True
        })
        _vertical_stitch(self.TEST_TASK_ID, {
            "center_vertical": {"resolution": [1000, 2000]},
            "side_vertical": {"resolution": [1000, 2000]},
            "center_count": 3,
            "side_count": 2,
        })
        _horizontal_stitch(self.TEST_TASK_ID, DEFAULT_HORIZONTAL_STITCH_CONF)
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_add_decoration_borders_integration(self):
        """测试装饰边框完整流程"""
        decoration_conf = {
            "input_dir": "combine_horizontal",
            "output_dir": "combine",
            "tire_design_width": 1000,
            "decoration_style": "simple",
            "decoration_border_alpha": 0.5,
            "decoration_gray_color": [128, 128, 128],
        }

        flag, details = _add_decoration_borders(self.TEST_TASK_ID, decoration_conf)

        assert flag is True
        assert "image_gen_number" in details

        task_dir = _RESULTS_DIR / f"task_id_{self.TEST_TASK_ID}"
        assert (task_dir / "combine").exists()


class TestExceptionScenarios:
    """异常场景集成测试"""

    TEST_TASK_ID = "test_exceptions"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_invalid_user_conf_type(self):
        """测试异常：无效 user_conf 类型"""
        flag, details = postprocessor(self.TEST_TASK_ID, 12345)

        assert flag is False
        assert details["failed_stage"] == "conf_processing"
        assert "err_msg" in details

    def test_json_file_not_found(self):
        """测试异常：JSON 文件不存在"""
        flag, details = postprocessor(self.TEST_TASK_ID, "/non/existent/config.json")

        assert flag is False
        assert details["failed_stage"] == "conf_processing"

    def test_vertical_stitch_empty_config(self):
        """测试异常：纵图拼接空配置"""
        flag, details = _vertical_stitch(self.TEST_TASK_ID, {})

        assert flag is False
        assert "err_msg" in details

    def test_horizontal_stitch_empty_config(self):
        """测试异常：横图拼接空配置"""
        flag, details = _horizontal_stitch(self.TEST_TASK_ID, {})

        assert flag is False
        assert "err_msg" in details

    def test_stage_failure_propagation(self):
        """测试异常：阶段失败传播"""
        from unittest.mock import patch

        with patch('services.postprocessor._small_image_filter',
                   return_value=(False, {"err_msg": "Pattern continuity failed"})):

            flag, details = postprocessor(self.TEST_TASK_ID, {})

            assert flag is False
            assert details["failed_stage"] == "small_image_filter"
```

### A.3 `tests/integration/services/test_postprocessor_pipeline.py`

```python
# -*- coding: utf-8 -*-
"""
postprocessor 全流程集成测试

测试完整 9 阶段流程的端到端正确性
"""

import pytest
import shutil
from pathlib import Path
from unittest.mock import patch

from services.postprocessor import postprocessor

# 项目根目录和测试数据目录
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_TEST_DATASETS_DIR = _PROJECT_ROOT / "tests" / "datasets" / "task_integration"
_RESULTS_DIR = _PROJECT_ROOT / ".results"


def prepare_task_integration_data(task_id: str) -> Path:
    """准备 task_integration 测试数据"""
    task_dir = _RESULTS_DIR / f"task_id_{task_id}"

    if task_dir.exists():
        shutil.rmtree(task_dir)

    task_dir.mkdir(parents=True, exist_ok=True)

    for inf_dir in ["center_inf", "side_inf"]:
        src = _TEST_DATASETS_DIR / inf_dir
        dst = task_dir / inf_dir
        if src.exists():
            shutil.copytree(src, dst)

    return task_dir


def cleanup_task_data(task_id: str):
    """清理任务测试数据"""
    task_dir = _RESULTS_DIR / f"task_id_{task_id}"
    if task_dir.exists():
        shutil.rmtree(task_dir)


class TestFullPipelineIntegration:
    """全流程端到端集成测试"""

    TEST_TASK_ID = "test_full_pipeline"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_full_pipeline_with_mock_todos(self):
        """测试全流程 - 使用 Mock 处理 TODO 阶段"""
        user_conf = {
            "tire_design_width": 1000,
            "decoration_style": "simple",
            "vertical_stitch_conf": {
                "center_vertical": {"resolution": [1000, 2000]},
                "side_vertical": {"resolution": [1000, 2000]},
                "center_count": 3,
                "side_count": 2,
            }
        }

        with patch('services.postprocessor._small_image_score',
                   return_value=(True, {"image_gen_number": 2})):
            with patch('services.postprocessor._calculate_total_score',
                       return_value=(True, {"total_score": 85.0})):
                with patch('services.postprocessor._standard_input',
                           return_value=(True, {"image_gen_number": 1})):

                    flag, details = postprocessor(self.TEST_TASK_ID, user_conf)

                    assert flag is True
                    assert "image_gen_number" in details
                    assert details["task_id"] == self.TEST_TASK_ID

    def test_full_pipeline_empty_config(self):
        """测试全流程 - 空配置"""
        with patch('services.postprocessor._small_image_score',
                   return_value=(True, {"image_gen_number": 0})):
            with patch('services.postprocessor._calculate_total_score',
                       return_value=(True, {"total_score": 0})):
                with patch('services.postprocessor._standard_input',
                           return_value=(True, {"image_gen_number": 0})):

                    flag, details = postprocessor(self.TEST_TASK_ID, {})

                    assert flag is True


class TestFullPipelineEdgeCases:
    """全流程边界情况测试"""

    TEST_TASK_ID = "test_pipeline_edge"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_pipeline_with_json_config(self, tmp_path):
        """测试全流程 - JSON 配置文件输入"""
        import json

        json_path = tmp_path / "config.json"
        user_conf = {
            "tire_design_width": 1200,
            "decoration_style": "simple"
        }
        with open(json_path, 'w') as f:
            json.dump(user_conf, f)

        with patch('services.postprocessor._small_image_score',
                   return_value=(True, {"image_gen_number": 2})):
            with patch('services.postprocessor._calculate_total_score',
                       return_value=(True, {"total_score": 85.0})):
                with patch('services.postprocessor._standard_input',
                           return_value=(True, {"image_gen_number": 1})):

                    flag, details = postprocessor(self.TEST_TASK_ID, str(json_path))

                    assert flag is True
```
