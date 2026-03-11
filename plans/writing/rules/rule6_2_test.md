# 纵图拼接重构测试用例设计 (rule6_2_test)

**创建日期**: 2026-03-11
**状态**: 待实施
**类型**: 单元测试

---

## 1. 目标

为纵图拼接重构后的代码编写单元测试，覆盖：
1. `algorithms/stitching/vertical_stitch.py::stitch_and_resize()` - 纯函数算法
2. `rules/rule6_2.py` - 中间层处理逻辑

---

## 2. 文件结构

```
tests/unittests/
├── algorithms/stitching/
│   └── test_vertical_stitch.py      # 重构：9 个测试用例
└── rules/
    └── test_rule6_2.py              # 新建：16 个测试用例
```

---

## 3. 测试用例清单

### 3.1 test_vertical_stitch.py (9 个测试用例)

**测试对象**: `stitch_and_resize(image, stitch_count, target_size)`
**测试框架**: pytest
**测试数据**: PIL 合成图片

| # | 测试用例 | 测试目的 | 输入参数 | 预期结果 |
|---|---------|---------|---------|---------|
| 1 | `test_stitch_and_resize_basic` | 基本功能测试 | 100x50 红图，stitch=3, target=(200,300) | 输出尺寸 200x300 |
| 2 | `test_stitch_and_resize_single_stitch` | 单次拼接 | 100x50 图，stitch=1, target=(100,50) | 输出尺寸 100x50 |
| 3 | `test_stitch_and_resize_multi_stitch` | 多次拼接 | 100x50 图，stitch=5 | 高度=250 |
| 4 | `test_stitch_and_resize_with_pattern` | 图案验证 | 带颜色渐变的图 | 拼接后图案连续 |
| 5 | `test_stitch_and_resize_invalid_stitch_zero` | 参数校验 | stitch_count=0 | 抛出 ValueError |
| 6 | `test_stitch_and_resize_invalid_stitch_negative` | 参数校验 | stitch_count=-1 | 抛出 ValueError |
| 7 | `test_stitch_and_resize_invalid_target_size_single` | 参数校验 | target_size=(100,) | 抛出 ValueError |
| 8 | `test_stitch_and_resize_invalid_target_size_triple` | 参数校验 | target_size=(100,100,100) | 抛出 ValueError |
| 9 | `test_stitch_and_resize_invalid_target_size_string` | 参数校验 | target_size="200x300" | 抛出 ValueError |

---

### 3.2 test_rule6_2.py (16 个测试用例)

**测试对象**: `process_vertical_stitch()`, `process_single_dir()`, 辅助函数
**测试框架**: pytest
**测试数据**: tests/datasets 中的真实图片 (center_filter/2.png, side_filter/0.png)

#### 辅助函数测试 (4 个)

| # | 测试用例 | 测试对象 | 测试目的 | 验证点 |
|---|---------|---------|---------|--------|
| 1 | `test_get_image_files` | `_get_image_files()` | 获取并排序图片 | 返回排序后的列表 |
| 2 | `test_get_image_files_empty` | `_get_image_files()` | 空目录 | 返回空列表 |
| 3 | `test_get_image_files_mixed_ext` | `_get_image_files()` | 混合扩展名 | 包含.png/.jpg/.jpeg/.bmp |
| 4 | `test_aggregate_summary` | `_aggregate_summary()` | 统计聚合 | 正确累加各目录计数 |

#### 单目录处理测试 (4 个)

| # | 测试用例 | 测试目的 | 输入 | 验证点 |
|---|---------|---------|------|--------|
| 5 | `test_process_single_dir_center` | center_filter 处理 | center_filter/2.png | 输出到 center_vertical，尺寸正确 |
| 6 | `test_process_single_dir_side` | side_filter 处理 | side_filter/0.png | 输出到 side_vertical，尺寸正确 |
| 7 | `test_process_single_dir_empty` | 空目录处理 | 空目录 | 返回成功，计数为 0 |
| 8 | `test_process_single_dir_missing_params` | 缺少必需参数 | stitch_count=None | 返回错误信息 |

#### 主入口测试 (6 个)

| # | 测试用例 | 测试目的 | 配置 | 验证点 |
|---|---------|---------|------|--------|
| 9 | `test_process_vertical_stitch_single_filter` | 单 filter | [center_filter] | 成功，返回统计信息 |
| 10 | `test_process_vertical_stitch_multiple_filters` | 多 filter | [center, side] | 两个目录都处理 |
| 11 | `test_process_vertical_stitch_empty_filters` | filters 为空 | [] | 返回 (False, err_msg) |
| 12 | `test_process_vertical_stitch_missing_dir` | 目录不存在 | [nonexistent] | 跳过，继续处理 |
| 13 | `test_process_vertical_stitch_missing_params` | 缺少参数 | [缺少 stitch_count] | 记录错误，继续其他 |
| 14 | `test_process_vertical_stitch_custom_suffix` | 自定义后缀 | output_dir_suffix="_custom" | 输出到 center_custom |

#### 错误处理测试 (2 个)

| # | 测试用例 | 测试目的 | 错误场景 | 验证点 |
|---|---------|---------|---------|--------|
| 15 | `test_error_handling_corrupt_image` | 损坏图片 | 输入损坏 PNG | 跳过该图片，继续下一张 |
| 16 | `test_error_handling_partial_failure` | 部分失败 | 多张图片中 1 张损坏 | 成功/失败计数正确 |

---

## 4. 测试数据

### 4.1 算法测试数据 (PIL 合成)

```python
# 基础测试图片
img = Image.new('RGB', (100, 50), color='red')

# 带图案的测试图片（用于验证拼接连续性）
img = Image.new('RGB', (100, 50))
for i in range(50):
    for j in range(100):
        img.putpixel((j, i), (i*5, j*2, 100))
```

### 4.2 中间层测试数据 (真实图片)

```
tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/
├── center_filter/
│   └── 2.png          # rule6_2 center 测试输入
└── side_filter/
    └── 0.png          # rule6_2 side 测试输入
```

### 4.3 测试输出目录

```
.results/task_id_test_rule6_2/
├── center_filter/     # 测试时复制的输入
├── side_filter/       # 测试时复制的输入
├── center_vertical/   # 输出（验证用）
└── side_vertical/     # 输出（验证用）
```

---

## 5. 关键验证点

### 5.1 算法层验证

- 输出图片尺寸正确
- 拼接后图案连续性
- 参数校验异常抛出

### 5.2 中间层验证

- 输出文件存在
- 输出图片尺寸正确（如 200x1241 或 400x1241）
- 统计信息准确（total_count, success_count, failed_count）
- 输出路径正确
- 错误处理符合预期（跳过、继续）

---

## 6. 测试代码结构示例

### 6.1 test_vertical_stitch.py

```python
# -*- coding: utf-8 -*-
"""
stitch_and_resize 纯函数单元测试
"""

import pytest
from PIL import Image
from algorithms.stitching.vertical_stitch import stitch_and_resize


class TestStitchAndResize:
    """stitch_and_resize 纯函数单元测试"""

    def test_stitch_and_resize_basic(self):
        """基本功能测试"""
        img = Image.new('RGB', (100, 50), color='red')
        result = stitch_and_resize(img, 3, (200, 300))
        assert result.size == (200, 300)

    def test_stitch_and_resize_single_stitch(self):
        """单次拼接测试"""
        img = Image.new('RGB', (100, 50), color='blue')
        result = stitch_and_resize(img, 1, (100, 50))
        assert result.size == (100, 50)

    def test_stitch_and_resize_multi_stitch(self):
        """多次拼接测试"""
        img = Image.new('RGB', (100, 50), color='green')
        result = stitch_and_resize(img, 5, (100, 250))
        assert result.size == (100, 250)

    def test_stitch_and_resize_with_pattern(self):
        """带图案图片的拼接验证"""
        # 创建带渐变的图片
        img = Image.new('RGB', (100, 50))
        for i in range(50):
            for j in range(100):
                img.putpixel((j, i), (i*5, j*2, 100))

        result = stitch_and_resize(img, 3, (200, 150))
        assert result.size == (200, 150)
        # 验证图案连续性：拼接处颜色应该连续
        pixel_top = result.getpixel((50, 49))
        pixel_bottom = result.getpixel((50, 50))
        # 拼接处相邻像素应该来自原图的不同位置，但颜色渐变应该连续
        assert abs(pixel_top[0] - pixel_bottom[0]) <= 10  # R 通道接近

    def test_stitch_and_resize_invalid_stitch_zero(self):
        """stitch_count=0 应该抛出 ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 0, (200, 300))

    def test_stitch_and_resize_invalid_stitch_negative(self):
        """stitch_count<0 应该抛出 ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, -1, (200, 300))

    def test_stitch_and_resize_invalid_target_size_single(self):
        """target_size 单元素应该抛出 ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 3, (100,))

    def test_stitch_and_resize_invalid_target_size_triple(self):
        """target_size 三元素应该抛出 ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 3, (100, 100, 100))

    def test_stitch_and_resize_invalid_target_size_string(self):
        """target_size 字符串应该抛出 ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 3, "200x300")
```

### 6.2 test_rule6_2.py

```python
# -*- coding: utf-8 -*-
"""
rule6_2 中间层单元测试
"""

import pytest
import shutil
from pathlib import Path
from PIL import Image

from rules.rule6_2 import (
    process_vertical_stitch,
    process_single_dir,
    _get_image_files,
    _aggregate_summary
)


class TestRule6_2:
    """rule6_2 中间层单元测试"""

    TEST_TASK_ID = "test_rule6_2"
    DATASET_BASE = Path("tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed")
    TEST_OUTPUT_BASE = Path(".results") / f"task_id_{TEST_TASK_ID}"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """测试准备和清理"""
        self._prepare_test_data()
        yield
        # 保留输出目录用于验证

    def _prepare_test_data(self):
        """准备测试数据"""
        # 清理旧目录
        if self.TEST_OUTPUT_BASE.exists():
            shutil.rmtree(self.TEST_OUTPUT_BASE)

        # 创建目录结构
        self.TEST_OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

        # 复制测试数据到 filter 目录
        for filter_name in ["center_filter", "side_filter"]:
            src = self.DATASET_BASE / filter_name
            dst = self.TEST_OUTPUT_BASE / filter_name
            if src.exists():
                shutil.copytree(src, dst)

    # ========== 辅助函数测试 ==========

    def test_get_image_files(self):
        """测试图片文件获取和排序"""
        center_filter_dir = self.TEST_OUTPUT_BASE / "center_filter"
        image_files = _get_image_files(center_filter_dir)

        assert len(image_files) > 0
        assert all(f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']
                   for f in image_files)
        # 验证排序
        names = [f.name for f in image_files]
        assert names == sorted(names)

    def test_get_image_files_empty(self):
        """测试空目录"""
        empty_dir = self.TEST_OUTPUT_BASE / "empty_filter"
        empty_dir.mkdir(parents=True, exist_ok=True)

        image_files = _get_image_files(empty_dir)
        assert len(image_files) == 0

    def test_get_image_files_mixed_ext(self):
        """测试混合扩展名"""
        # 创建混合扩展名测试数据
        mixed_dir = self.TEST_OUTPUT_BASE / "mixed_filter"
        mixed_dir.mkdir(parents=True, exist_ok=True)

        # 创建不同扩展名的测试图片
        img = Image.new('RGB', (50, 50), color='red')
        img.save(mixed_dir / "test1.png", "PNG")
        img.save(mixed_dir / "test2.jpg", "JPEG")

        image_files = _get_image_files(mixed_dir)
        assert len(image_files) == 2
        extensions = set(f.suffix.lower() for f in image_files)
        assert '.png' in extensions
        assert '.jpg' in extensions

    def test_aggregate_summary(self):
        """测试统计聚合"""
        dir_stats = {
            "center_filter": {
                "total_count": 5,
                "processed_count": 5,
                "success_count": 4,
                "failed_count": 1,
                "skipped_count": 0
            },
            "side_filter": {
                "total_count": 3,
                "processed_count": 3,
                "success_count": 3,
                "failed_count": 0,
                "skipped_count": 0
            }
        }

        summary = _aggregate_summary(dir_stats)

        assert summary["total_images"] == 8
        assert summary["total_processed"] == 8
        assert summary["total_success"] == 7
        assert summary["total_failed"] == 1
        assert summary["total_skipped"] == 0

    # ========== 单目录处理测试 ==========

    def test_process_single_dir_center(self):
        """测试 center_filter 处理"""
        input_dir = self.TEST_OUTPUT_BASE / "center_filter"
        output_dir = self.TEST_OUTPUT_BASE / "center_vertical"

        flag, stats = process_single_dir(
            input_dir=input_dir,
            output_dir=output_dir,
            stitch_count=5,
            target_size=(200, 1241),
            task_id=self.TEST_TASK_ID,
            filter_dir="center_filter"
        )

        assert flag is True
        assert stats["total_count"] > 0
        assert stats["success_count"] == stats["total_count"]
        assert output_dir.exists()

        # 验证输出图片尺寸
        for img_name in ["2.png"]:
            output_path = output_dir / img_name
            if output_path.exists():
                img = Image.open(output_path)
                assert img.size == (200, 1241)

    def test_process_single_dir_side(self):
        """测试 side_filter 处理"""
        input_dir = self.TEST_OUTPUT_BASE / "side_filter"
        output_dir = self.TEST_OUTPUT_BASE / "side_vertical"

        flag, stats = process_single_dir(
            input_dir=input_dir,
            output_dir=output_dir,
            stitch_count=5,
            target_size=(400, 1241),
            task_id=self.TEST_TASK_ID,
            filter_dir="side_filter"
        )

        assert flag is True
        assert stats["total_count"] > 0
        assert stats["success_count"] == stats["total_count"]
        assert output_dir.exists()

        # 验证输出图片尺寸
        for img_name in ["0.png"]:
            output_path = output_dir / img_name
            if output_path.exists():
                img = Image.open(output_path)
                assert img.size == (400, 1241)

    def test_process_single_dir_empty(self):
        """测试空目录处理"""
        empty_dir = self.TEST_OUTPUT_BASE / "empty_filter"
        empty_dir.mkdir(parents=True, exist_ok=True)
        output_dir = self.TEST_OUTPUT_BASE / "empty_vertical"

        flag, stats = process_single_dir(
            input_dir=empty_dir,
            output_dir=output_dir,
            stitch_count=5,
            target_size=(200, 1241),
            task_id=self.TEST_TASK_ID,
            filter_dir="empty_filter"
        )

        assert flag is True
        assert stats["total_count"] == 0
        assert stats["success_count"] == 0

    def test_process_single_dir_missing_params(self):
        """测试缺少必需参数"""
        input_dir = self.TEST_OUTPUT_BASE / "center_filter"
        output_dir = self.TEST_OUTPUT_BASE / "center_vertical_test"

        # stitch_count=None 应该在调用前被检测到
        # 这里测试 process_vertical_stitch 层的参数校验
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": None,  # 缺少必需参数
                    "resolution": [200, 1241]
                }
            ]
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True  # 整体成功，但该 filter 失败
        assert "center_filter" in details["directories"]
        assert "err_msg" in details["directories"]["center_filter"]

    # ========== 主入口测试 ==========

    def test_process_vertical_stitch_single_filter(self):
        """测试单 filter 处理"""
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": 5,
                    "resolution": [200, 1241]
                }
            ],
            "output_dir_suffix": "_vertical"
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True
        assert "directories" in details
        assert "summary" in details
        assert "center_filter" in details["directories"]

    def test_process_vertical_stitch_multiple_filters(self):
        """测试多 filter 处理"""
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": 5,
                    "resolution": [200, 1241]
                },
                {
                    "dir": "side_filter",
                    "stitch_count": 5,
                    "resolution": [400, 1241]
                }
            ],
            "output_dir_suffix": "_vertical"
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True
        assert "center_filter" in details["directories"]
        assert "side_filter" in details["directories"]

    def test_process_vertical_stitch_empty_filters(self):
        """测试 filters 为空"""
        conf = {
            "base_path": ".results",
            "filters": []
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is False
        assert "err_msg" in details
        assert "filters 不能为空" in details["err_msg"]

    def test_process_vertical_stitch_missing_dir(self):
        """测试目录不存在"""
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "nonexistent_filter",
                    "stitch_count": 5,
                    "resolution": [200, 1241]
                }
            ]
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True  # 整体成功，但该目录被跳过
        assert "nonexistent_filter" in details["directories"]

    def test_process_vertical_stitch_missing_params(self):
        """测试 filter 缺少必需参数"""
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": None,  # 缺少必需参数
                    "resolution": [200, 1241]
                }
            ]
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True
        assert "center_filter" in details["directories"]
        assert "err_msg" in details["directories"]["center_filter"]

    def test_process_vertical_stitch_custom_suffix(self):
        """测试自定义输出目录后缀"""
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": 5,
                    "resolution": [200, 1241]
                }
            ],
            "output_dir_suffix": "_custom"
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True
        # 验证输出目录是 center_custom 而不是 center_vertical
        output_dir = self.TEST_OUTPUT_BASE / "center_custom"
        assert output_dir.exists()

    # ========== 错误处理测试 ==========

    def test_error_handling_corrupt_image(self):
        """测试损坏图片处理"""
        # 创建损坏的图片文件
        corrupt_dir = self.TEST_OUTPUT_BASE / "corrupt_filter"
        corrupt_dir.mkdir(parents=True, exist_ok=True)

        # 写入无效的 PNG 数据
        corrupt_file = corrupt_dir / "corrupt.png"
        corrupt_file.write_bytes(b"not a valid png file")

        output_dir = self.TEST_OUTPUT_BASE / "corrupt_vertical"

        flag, stats = process_single_dir(
            input_dir=corrupt_dir,
            output_dir=output_dir,
            stitch_count=5,
            target_size=(200, 1241),
            task_id=self.TEST_TASK_ID,
            filter_dir="corrupt_filter"
        )

        # 损坏图片应该被跳过，但不影响整体成功
        assert flag is True
        assert stats["failed_count"] == 1
        assert stats["images"]["corrupt.png"]["status"] == "failed"

    def test_error_handling_partial_failure(self):
        """测试部分失败场景"""
        # 创建混合数据：好图片 + 坏图片
        mixed_dir = self.TEST_OUTPUT_BASE / "partial_filter"
        mixed_dir.mkdir(parents=True, exist_ok=True)

        # 添加好图片
        good_img = Image.new('RGB', (50, 50), color='red')
        good_img.save(mixed_dir / "good.png", "PNG")

        # 添加坏图片
        corrupt_file = mixed_dir / "bad.png"
        corrupt_file.write_bytes(b"invalid png")

        output_dir = self.TEST_OUTPUT_BASE / "partial_vertical"

        flag, stats = process_single_dir(
            input_dir=mixed_dir,
            output_dir=output_dir,
            stitch_count=5,
            target_size=(200, 1241),
            task_id=self.TEST_TASK_ID,
            filter_dir="partial_filter"
        )

        assert flag is True
        assert stats["total_count"] == 2
        assert stats["success_count"] == 1
        assert stats["failed_count"] == 1
```

---

## 7. 实施步骤

### Step 1: 重构 `test_vertical_stitch.py`

- 删除原有基于 `VerticalStitch` 类的测试
- 编写基于 `stitch_and_resize` 纯函数的 9 个测试用例
- 使用 PIL 合成测试图片

### Step 2: 创建 `test_rule6_2.py`

- 编写 4 个辅助函数测试
- 编写 4 个单目录处理测试
- 编写 6 个主入口测试
- 编写 2 个错误处理测试

### Step 3: 运行测试验证

```bash
source .setup_giti_speckit_py12.sh
pytest tests/unittests/algorithms/stitching/test_vertical_stitch.py -v
pytest tests/unittests/rules/test_rule6_2.py -v
```

---

## 8. 注意事项

1. **测试数据隔离**: 每个测试使用独立的 task_id，避免相互干扰
2. **输出目录保留**: 测试后保留输出目录，便于人工验证
3. **图片尺寸验证**: rule6_2 测试中必须验证输出图片的实际尺寸
4. **错误处理**: 验证错误场景下的行为符合预期（跳过、继续）
5. **不测试 postprocessor 层**: 只测试算法和中间层，不涉及 postprocessor 集成

---

## 9. 备注

- 本计划已确认，待实施
- 实施时严格按照本计划执行
- 所有测试都是单元测试，不涉及集成测试
