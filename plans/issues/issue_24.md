# Issue #24: BUG:tmp 兼容性&异常处理

**Issue URL**: https://github.com/ydhh-test/giti-tire-ai-pattern/issues/24

**创建日期**: 2026-03-12

---

## Bug 描述

### Bug 1: `/tmp` 目录兼容性问题

Windows 不支持 `/tmp` 目录，需要改为 `.results/tmp`。

**涉及文件**:
- `tests/unittests/services/test_postprocessor.py`

**说明**: 经检查，`test_postprocessor_pipeline.py` 和 `test_cv_utils.py` 使用的是 pytest 的 `tmp_path` fixture（跨平台兼容），无需修改。只有 `test_postprocessor.py` 中的 `TestLoadUserConf` 和 `TestStageFunctions` 测试类使用了硬编码的 `Path("/tmp/...")`。

### Bug 2: `pattern_continuity.py` 异常处理逻辑不对

当前异常处理使用 `raise`，需要改为返回 `None` 和错误信息字典。

**涉及文件**:
- `algorithms/detection/pattern_continuity.py`（主函数异常处理）
- `rules/rule6_1.py`（调用方检查返回值）

---

## 修复计划

### Bug 1: `/tmp` 目录兼容性

#### 修改 1: `TestLoadUserConf` 测试类迁移

**位置**: `tests/unittests/services/test_postprocessor.py` 第 95-144 行

**修改前**:
```python
class TestLoadUserConf(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("/tmp/test_postprocessor")
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
```

**修改后**:
```python
class TestLoadUserConf:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.test_dir = tmp_path / "test_postprocessor"
        # pytest 自动清理，无需 tearDown
```

#### 修改 2: `TestStageFunctions` 测试类迁移

**位置**: `tests/unittests/services/test_postprocessor.py` 第 179-218 行

**修改前**:
```python
class TestStageFunctions(unittest.TestCase):
    def setUp(self):
        self.task_id = "test_task"
        self.test_dir = Path("/tmp/test_postprocessor_stages")
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
```

**修改后**:
```python
class TestStageFunctions:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.task_id = "test_task"
        self.test_dir = tmp_path / "test_postprocessor_stages"
        # pytest 自动清理，无需 tearDown
```

#### 修改 3: 新增正例测试类

**位置**: `tests/unittests/services/test_postprocessor.py`

**目的**: 留下实际输出供检查，测试后不清理

**新增内容**:
```python
class TestPositiveExample:
    """正例测试 - 输出保留供检查"""

    @pytest.mark.trylast
    @pytest.fixture(autouse=True)
    def setup(self):
        """设置固定输出目录，测试后不清理"""
        self.output_dir = Path(".results/tmp/positive_example")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        yield
        # 不清理输出，供人工检查

    def test_positive_example(self):
        """正例测试 - 验证基本功能并保留输出"""
        # 测试逻辑，输出到 self.output_dir
        pass
```

---

### Bug 2: `pattern_continuity.py` 异常处理

#### 修改 1: 主函数异常处理

**位置**: `algorithms/detection/pattern_continuity.py` 第 170-176 行

**修改前**:
```python
except (PatternDetectionError, ImageDimensionError, ContinuityAnalysisError):
    # 重新抛出我们的自定义异常
    raise
except Exception as e:
    # 捕获其他异常并转换为 PatternDetectionError
    logger.error(f"图案连续性检测时发生未知错误：{str(e)}")
    raise PatternDetectionError(f"未知错误：{str(e)}")
```

**修改后**:
```python
except Exception as e:
    err_msg = str(e)
    error_type = type(e).__name__
    logger.error(f"图案连续性检测失败：{err_msg}")
    return None, {'err_msg': err_msg, 'error_type': error_type}
```

#### 修改 2: 调用方检查返回值

**位置**: `rules/rule6_1.py` `process_pattern_continuity_single_dir()` 函数中（第 160-168 行附近）

**修改前**:
```python
score, details = detect_pattern_continuity(
    image=gray,
    conf=pattern_continuity_conf,
    task_id=task_id,
    image_type=filter_dir,
    image_id=str(image_id),
    visualize=visualize,
    output_base_dir=str(vis_output_dir)
)

# 判断连续性
is_continuous = details.get('is_continuous', False)
```

**修改后**:
```python
score, details = detect_pattern_continuity(
    image=gray,
    conf=pattern_continuity_conf,
    task_id=task_id,
    image_type=filter_dir,
    image_id=str(image_id),
    visualize=visualize,
    output_base_dir=str(vis_output_dir)
)

# 检查是否返回错误
if score is None:
    err_msg = details.get('err_msg', '未知错误')
    error_type = details.get('error_type', 'UnknownError')
    logger.error(f"图案连续性检测失败，图片路径：{image_path}, "
                 f"错误类型：{error_type}, 错误信息：{err_msg}")
    stats["images"][image_path.name] = {
        "error": err_msg,
        "error_type": error_type,
        "deleted": True
    }
    stats["deleted_count"] += 1
    continue

# 判断连续性
is_continuous = details.get('is_continuous', False)
```

---

## 修改文件清单

| 文件 | 修改内容 |
|------|---------|
| `tests/unittests/services/test_postprocessor.py` | 1. `TestLoadUserConf` 迁移到 pytest 风格 |
| | 2. `TestStageFunctions` 迁移到 pytest 风格 |
| | 3. 新增 `TestPositiveExample` 测试类 |
| `algorithms/detection/pattern_continuity.py` | 主函数异常处理改为返回 `None, {err_msg, error_type}` |
| `rules/rule6_1.py` | 调用方检查 `score is None`，记录错误后 `continue` |

---

## 注意事项

1. **Bug 1 修改范围**: 只修改 `test_postprocessor.py`，另外两个测试文件使用的是 pytest 的 `tmp_path` fixture，无需修改。

2. **正例测试原则**: 正例测试类使用 `@pytest.mark.trylast` 确保最后执行，输出到 `.results/tmp/positive_example` 目录，测试后不清理，供人工检查。

3. **Bug 2 异常返回格式**: 返回 `None, {'err_msg': str(e), 'error_type': type(e).__name__}`。

4. **Bug 2 调用方处理**: 检测到 `score is None` 时，记录错误图片路径、错误类型、错误信息，然后 `continue` 处理下一张图片。

---

## 实施步骤

1. [ ] 修改 `test_postprocessor.py` - `TestLoadUserConf` 迁移到 pytest 风格
2. [ ] 修改 `test_postprocessor.py` - `TestStageFunctions` 迁移到 pytest 风格
3. [ ] 修改 `test_postprocessor.py` - 新增 `TestPositiveExample` 测试类
4. [ ] 修改 `pattern_continuity.py` - 主函数异常处理
5. [ ] 修改 `rule6_1.py` - 调用方检查返回值
