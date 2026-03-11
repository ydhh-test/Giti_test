# rule19 装饰边框中间层实现计划

**创建日期**: 2026-03-11
**状态**: 待实施

---

## 一、需求概述

在 `rules/rule19.py` 创建中间层，实现图片文件夹的循环，将流程入口 `services/postprocessor.py::_add_decoration_borders` 和算法实现 `utils/cv_utils.py::add_gray_borders` 调用起来。

### 架构目标

```
postprocessor() [services/postprocessor.py]
  ↓
  _add_decoration_borders(task_id, decoration_conf)
  ↓
  process_decoration_borders(task_id, decoration_conf) [rules/rule19.py] ← 新增中间层
  ↓
  add_gray_borders(image, conf) [utils/cv_utils.py]
```

---

## 二、设计决策

### 2.1 配置结构

```python
decoration_conf = {
    "input_dir": "combine_horizontal",      # 输入目录名
    "output_dir": "combine",                 # 输出目录名
    "tire_design_width": 1000,               # 花纹有效宽度 (默认来自 UserConfig)
    "decoration_border_alpha": 0.5,          # 透明度 (默认来自 UserConfig)
    "decoration_gray_color": (135, 135, 135) # 灰色 RGB (默认来自 UserConfig)
}
```

### 2.2 目录结构

```
.results/task_id_{task_id}/
├── {input_dir}/           # 输入目录 (如 combine_horizontal)
│   ├── image1.png
│   └── image2.png
└── {output_dir}/          # 输出目录 (如 combine)
    ├── image1.png         # 添加灰边后的输出
    └── image2.png
```

### 2.3 关键设计决策

| 决策点 | 选择 |
|--------|------|
| tire_design_width 默认值 | 1000 |
| 配置注入时机 | Stage 1 (Conf 处理) |
| 配置传递方式 | 方案 B (decoration_conf 本身包含参数) |
| 返回格式 | 统一格式 (directories + summary) |
| postprocessor 格式转换 | 在 `_add_decoration_borders` 中转换 |
| image_score 填充 | 暂时 0.0 和 None |
| 测试数据集 | 复用 task_id_test_rule13 (1480×1241) |
| 测试 tire_design_width | 显式指定 1000 |

---

## 三、任务分解

### Task 1: 更新 configs/user_config.py

**目标**: 修改 `tire_design_width` 默认值

**修改位置**: 第 119 行

```python
# 当前:
tire_design_width: int = 700

# 修改为:
tire_design_width: int = 1000
```

---

### Task 2: 创建 rules/rule19.py

**目标**: 实现装饰边框中间层

**文件结构**:

```python
# -*- coding: utf-8 -*-
"""
rule19: 装饰边框中间层

功能:
- 接收 postprocessor 的调用
- 循环 input_dir 目录中的所有图片
- 调用 add_gray_borders() 添加装饰边框
- 保存到 output_dir 目录

目录关系:
- 输入：.results/task_id_{task_id}/{input_dir}/*.png
- 输出：.results/task_id_{task_id}/{output_dir}/*.png
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
import cv2

from utils.logger import get_logger

logger = get_logger("rule19")


def process_decoration_borders(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    装饰边框主入口

    参数:
        task_id: 任务 ID
        conf: 配置字典
            - input_dir: 输入目录名 (默认 "combine_horizontal")
            - output_dir: 输出目录名 (默认 "combine")
            - tire_design_width: 花纹有效宽度 (像素)
            - decoration_border_alpha: 透明度 (0~1)
            - decoration_gray_color: 灰色 RGB 值
            - output_base_dir: 输出基础目录 (默认 ".results")

    返回:
        (True, 详细统计字典) 或 (False, 错误信息)
    """
    # Step 1: 从 conf 读取配置参数
    input_dir = conf.get("input_dir", "combine_horizontal")
    output_dir = conf.get("output_dir", "combine")
    output_base_dir = conf.get("output_base_dir", ".results")

    # Step 2: 构建输入输出路径
    base_path = Path(output_base_dir) / f"task_id_{task_id}"
    input_path = base_path / input_dir
    output_path = base_path / output_dir

    # Step 3: 检查输入目录是否存在
    if not input_path.exists():
        # 目录不存在，返回空统计
        return True, _build_empty_result(input_dir)

    # Step 4: 获取图片列表
    image_files = _get_image_files(input_path)

    if not image_files:
        # 目录为空，返回空统计
        return True, _build_empty_result(input_dir)

    # Step 5: 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)

    # Step 6: 循环处理每张图片
    image_results = []
    images_dict = {}

    for image_id, image_file in enumerate(image_files):
        flag, result = process_single_image(
            image_path=image_file,
            task_id=task_id,
            conf=conf,
            image_id=image_id,
            output_dir=output_path
        )

        if flag:
            image_results.append(result)
            images_dict[image_file.name] = result
        else:
            # 处理失败
            images_dict[image_file.name] = {
                "status": "failed",
                "error": result.get("err_msg", "未知错误")
            }
            logger.error(f"处理图片失败 {image_file.name}: {result.get('err_msg', '未知错误')}")

    # Step 7: 聚合统计信息
    summary = _aggregate_summary(image_results)

    return True, {
        "task_id": task_id,
        "directories": {
            output_dir: {
                "total_count": len(image_files),
                "processed_count": summary["total_processed"],
                "failed_count": summary["total_failed"],
                "images": images_dict
            }
        },
        "summary": summary
    }


def process_single_image(
    image_path: Path,
    task_id: str,
    conf: dict,
    image_id: int,
    output_dir: Path
) -> Tuple[bool, Dict[str, Any]]:
    """
    单张图片装饰边框处理

    参数:
        image_path: 图片路径
        task_id: 任务 ID
        conf: 配置字典
        image_id: 图片序号
        output_dir: 输出目录

    返回:
        (True, 处理结果) 或 (False, 错误信息)
    """
    from utils.cv_utils import add_gray_borders

    try:
        # Step 1: 读取图片
        img = cv2.imread(str(image_path))
        if img is None:
            return False, {"err_msg": "图片读取失败"}

        # Step 2: 调用 add_gray_borders
        result_img = add_gray_borders(img, conf)

        # Step 3: 保存结果
        output_path = output_dir / image_path.name
        cv2.imwrite(str(output_path), result_img)

        # Step 4: 构建返回结果
        return True, {
            "image_id": str(image_id),
            "image_name": image_path.name,
            "status": "success",
            "input_path": str(image_path),
            "output_path": str(output_path)
        }

    except Exception as e:
        logger.error(f"处理图片 {image_path.name} 异常：{str(e)}")
        return False, {"err_msg": str(e)}


# ========== 辅助函数 ==========

def _get_image_files(dir_path: Path) -> List[Path]:
    """获取目录内所有图片文件，按文件名排序"""
    extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    image_files = []
    for ext in extensions:
        image_files.extend(dir_path.glob(f"*{ext}"))
    return sorted(image_files, key=lambda x: x.name)


def _aggregate_summary(image_results: List[Dict[str, Any]]) -> dict:
    """聚合所有图片的统计信息"""
    total_count = len(image_results)
    processed_count = sum(1 for r in image_results if r.get("status") == "success")
    failed_count = total_count - processed_count

    return {
        "total_images": total_count,
        "total_processed": processed_count,
        "total_failed": failed_count
    }


def _build_empty_result(input_dir: str) -> dict:
    """构建空结果"""
    return {
        "task_id": None,
        "directories": {
            input_dir: {
                "total_count": 0,
                "processed_count": 0,
                "failed_count": 0,
                "images": {}
            }
        },
        "summary": {
            "total_images": 0,
            "total_processed": 0,
            "total_failed": 0
        }
    }
```

---

### Task 3: 更新 services/postprocessor.py

**目标**: 适配新的中间层调用方式

#### 修改点 1: 在 Stage 1 注入 decoration_conf 参数

在 `_merge_conf_from_complete_config` 函数中或 `postprocessor` 函数中，添加：

```python
# 在 merged_conf 构建完成后，注入 decoration_conf 参数
decoration_conf = merged_conf.get("decoration_conf", {})
# 从 merged_conf 提取参数注入到 decoration_conf
decoration_conf["tire_design_width"] = merged_conf.get("tire_design_width")
decoration_conf["decoration_border_alpha"] = merged_conf.get("decoration_border_alpha")
decoration_conf["decoration_gray_color"] = merged_conf.get("decoration_gray_color")
decoration_conf["decoration_style"] = merged_conf.get("decoration_style")
# 将注入后的 decoration_conf 放回 merged_conf
merged_conf["decoration_conf"] = decoration_conf
```

#### 修改点 2: 更新 `_add_decoration_borders` 函数签名

```python
# 当前:
def _add_decoration_borders(task_id: str, conf: dict, merged_conf: dict) -> tuple[bool, dict]:

# 修改为:
def _add_decoration_borders(task_id: str, decoration_conf: dict) -> tuple[bool, dict]:
```

#### 修改点 3: 更新 `_add_decoration_borders` 内部实现

```python
def _add_decoration_borders(task_id: str, decoration_conf: dict) -> tuple[bool, dict]:
    """
    添加装饰边框 - 调用 rule19 中间层

    Args:
        task_id: 任务 ID
        decoration_conf: 装饰边框配置 (已注入 tire_design_width 等参数)

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from rules.rule19 import process_decoration_borders

    # 调用 rule19 中间层
    flag, details = process_decoration_borders(task_id, decoration_conf)

    if not flag:
        return False, {
            "err_msg": details.get("err_msg", "装饰边框处理失败"),
            "task_id": task_id
        }

    # 将 rule19 返回格式转换为 postprocessor 需要的格式
    output_dir = decoration_conf.get("output_dir", "combine")
    images_dict = details.get("directories", {}).get(output_dir, {}).get("images", {})

    # 构建符合 postprocessor 格式的 details
    image_gen_number = len([img for img in images_dict.values() if img.get("status") == "success"])

    converted_details = {
        "image_gen_number": image_gen_number,
        "decoration_style": decoration_conf.get("decoration_style", "simple"),
        "tdw": decoration_conf.get("tire_design_width"),
        "alpha": decoration_conf.get("decoration_border_alpha", 0.5)
    }

    # 按文件名字母序添加每张图片信息
    sorted_images = sorted(
        [(name, img) for name, img in images_dict.items() if img.get("status") == "success"],
        key=lambda x: x[0]
    )

    for idx, (image_name, image_data) in enumerate(sorted_images):
        converted_details[str(idx)] = {
            "image_score": 0.0,  # 暂时填 0.0，留给后续阶段填充
            "image_path": image_data.get("output_path", ""),
            "image_score_details": None  # 暂时填 None，留给后续阶段填充
        }

    return True, converted_details
```

#### 修改点 4: 更新调用处

```python
# 当前 (第 171 行):
flag, details = _add_decoration_borders(task_id, decoration_conf, merged_conf)

# 修改为:
flag, details = _add_decoration_borders(task_id, decoration_conf)
```

---

### Task 4: 创建 tests/unittests/rules/test_rule19.py

**目标**: 为 rule19 编写完整的单元测试

**测试文件结构**:

```python
# -*- coding: utf-8 -*-
"""
rule19 单元测试 - 装饰边框中间层
"""

import pytest
import shutil
import cv2
import numpy as np
from pathlib import Path

from rules.rule19 import (
    process_decoration_borders,
    process_single_image,
    _get_image_files,
    _aggregate_summary,
    _build_empty_result
)


class TestRule19:
    """rule19 测试类"""

    TEST_TASK_ID = "test_rule19"
    TEST_OUTPUT_BASE = Path(".results") / f"task_id_{TEST_TASK_ID}"
    DATASET_BASE = Path("tests/datasets/task_id_test_rule13")

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, request):
        """每个测试前的准备"""
        is_full_test = request.function.__name__ == "test_process_decoration_borders_full"

        if not is_full_test:
            self._cleanup_test_data()

        yield
        # 测试后不清理，便于手动验证

    def _cleanup_test_data(self):
        """清理测试数据"""
        if self.TEST_OUTPUT_BASE.exists():
            shutil.rmtree(self.TEST_OUTPUT_BASE)

    def _copy_test_data(self) -> int:
        """
        复制测试数据到输入目录
        从 tests/datasets/task_id_test_rule13/combine_horizontal/
        复制到 .results/task_id_test_rule19/combine_horizontal/
        """
        src_dir = self.DATASET_BASE / "combine_horizontal"
        dst_dir = self.TEST_OUTPUT_BASE / "combine_horizontal"

        if not src_dir.exists():
            return 0

        dst_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for img_file in src_dir.glob("*.png"):
            shutil.copy2(str(img_file), str(dst_dir / img_file.name))
            count += 1

        return count

    # ========== 辅助函数测试 ==========

    def test_get_image_files(self):
        """测试图片文件获取"""
        test_dir = self.TEST_OUTPUT_BASE / "test_get_image_files"
        test_dir.mkdir(parents=True, exist_ok=True)

        # 创建测试图片文件
        for name in ["c.png", "a.png", "b.png"]:
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imwrite(str(test_dir / name), img)

        image_files = _get_image_files(test_dir)

        assert len(image_files) == 3
        names = [f.name for f in image_files]
        assert names == ["a.png", "b.png", "c.png"]

    def test_aggregate_summary(self):
        """测试统计聚合"""
        image_results = [
            {"status": "success"},
            {"status": "success"},
            {"status": "failed"},
            {"status": "success"},
        ]

        summary = _aggregate_summary(image_results)

        assert summary["total_images"] == 4
        assert summary["total_processed"] == 3
        assert summary["total_failed"] == 1

    def test_build_empty_result(self):
        """测试空结果构建"""
        result = _build_empty_result("test_input")

        assert result["task_id"] is None
        assert result["summary"]["total_images"] == 0

    # ========== 边界情况测试 ==========

    def test_process_decoration_borders_nonexistent_dir(self):
        """测试输入目录不存在的情况"""
        conf = {
            "input_dir": "nonexistent_dir",
            "output_dir": "combine",
            "tire_design_width": 1000,
            "decoration_border_alpha": 0.5,
            "decoration_gray_color": (135, 135, 135),
            "output_base_dir": str(self.TEST_OUTPUT_BASE.parent)
        }

        flag, details = process_decoration_borders(self.TEST_TASK_ID, conf)

        assert flag is True
        assert details["summary"]["total_images"] == 0

    def test_process_decoration_borders_empty_dir(self):
        """测试输入目录为空的情况"""
        # 创建空目录
        empty_dir = self.TEST_OUTPUT_BASE / "empty_input"
        empty_dir.mkdir(parents=True, exist_ok=True)

        conf = {
            "input_dir": "empty_input",
            "output_dir": "combine",
            "tire_design_width": 1000,
            "decoration_border_alpha": 0.5,
            "decoration_gray_color": (135, 135, 135),
            "output_base_dir": str(self.TEST_OUTPUT_BASE.parent)
        }

        flag, details = process_decoration_borders(self.TEST_TASK_ID, conf)

        assert flag is True
        assert details["summary"]["total_images"] == 0

    # ========== 单图处理测试 ==========

    def test_process_single_image(self):
        """测试单张图片处理"""
        # 创建测试图片
        input_dir = self.TEST_OUTPUT_BASE / "test_single_input"
        input_dir.mkdir(parents=True, exist_ok=True)
        image_path = input_dir / "test_single.png"

        # 创建 1480x1241 测试图片 (与测试数据集尺寸一致)
        img = np.zeros((1241, 1480, 3), dtype=np.uint8)
        img[:, :] = [120, 120, 120]  # 灰色背景
        cv2.imwrite(str(image_path), img)

        output_dir = self.TEST_OUTPUT_BASE / "test_single_output"
        output_dir.mkdir(parents=True, exist_ok=True)

        conf = {
            "tire_design_width": 1000,
            "decoration_border_alpha": 0.5,
            "decoration_gray_color": (135, 135, 135)
        }

        flag, result = process_single_image(
            image_path=image_path,
            task_id=self.TEST_TASK_ID,
            conf=conf,
            image_id=0,
            output_dir=output_dir
        )

        assert flag is True
        assert result["status"] == "success"
        assert result["image_name"] == "test_single.png"

        # 验证输出文件存在
        assert Path(result["output_path"]).exists()

    # ========== 完整流程测试 ==========

    def test_process_decoration_borders_full(self):
        """
        完整流程测试 - 使用真实测试数据

        测试场景:
        - 从 tests/datasets/task_id_test_rule13/combine_horizontal/ 复制 3 张图片
        - 执行完整的装饰边框处理
        - 验证返回值、输出文件
        """
        # Step 0: 清理旧目录
        self._cleanup_test_data()

        # Step 1: 准备测试数据
        copied_count = self._copy_test_data()
        assert copied_count == 3, f"预期复制 3 张图片，实际复制 {copied_count} 张"

        # Step 2: 准备配置 (显式指定 tire_design_width)
        conf = {
            "input_dir": "combine_horizontal",
            "output_dir": "combine",
            "tire_design_width": 1000,  # 显式指定
            "decoration_border_alpha": 0.5,
            "decoration_gray_color": (135, 135, 135),
            "output_base_dir": str(self.TEST_OUTPUT_BASE.parent)
        }

        # Step 3: 调用函数
        flag, details = process_decoration_borders(self.TEST_TASK_ID, conf)

        # Step 4: 验证返回值结构
        assert flag is True
        assert "task_id" in details
        assert "directories" in details
        assert "summary" in details

        # Step 5: 验证统计信息
        summary = details["summary"]
        assert summary["total_images"] == 3
        assert summary["total_processed"] == 3
        assert summary["total_failed"] == 0

        # Step 6: 验证每张图片的处理结果
        images = details["directories"]["combine"]["images"]
        assert len(images) == 3

        for image_name, image_data in images.items():
            assert image_data["status"] == "success"
            assert "output_path" in image_data
            # 验证输出文件存在
            assert Path(image_data["output_path"]).exists()

        # Step 7: 打印调试信息
        print(f"\n=== 完整流程测试通过 ===")
        print(f"输出目录：{self.TEST_OUTPUT_BASE / 'combine'}")
        print(f"处理图片数：{summary['total_processed']}")
        for image_name, image_data in images.items():
            print(f"  {image_name}: {image_data['status']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

### Task 5: 更新 tests/unittests/services/test_postprocessor.py

**目标**: 更新 `_add_decoration_borders` 相关测试

#### 修改点 1: 更新 `test_add_decoration_borders_success`

```python
def test_add_decoration_borders_success(self):
    """测试装饰边框成功处理"""
    decoration_conf = {
        "input_dir": "combine",
        "output_dir": "rst",
        "tire_design_width": 1000,
        "decoration_style": "simple",
        "decoration_border_alpha": 0.5
    }

    # 验证配置存在
    self.assertIn("tire_design_width", decoration_conf)
    self.assertEqual(decoration_conf["decoration_style"], "simple")
```

#### 修改点 2: 更新 `test_add_decoration_borders_missing_tdw`

```python
def test_add_decoration_borders_missing_tdw(self):
    """测试缺少 tire_design_width 配置"""
    decoration_conf = {
        "input_dir": "combine",
        "output_dir": "rst",
        "decoration_style": "simple"
        # tire_design_width 缺失
    }

    flag, details = _add_decoration_borders(self.task_id, decoration_conf)

    # 根据实现决定期望行为
```

#### 修改点 3: 更新 `test_add_decoration_borders_combine_dir_not_found`

```python
def test_add_decoration_borders_input_dir_not_found(self):
    """测试输入目录不存在"""
    decoration_conf = {
        "input_dir": "nonexistent_dir",
        "output_dir": "rst",
        "tire_design_width": 1000,
        "decoration_style": "simple"
    }

    flag, details = _add_decoration_borders(self.task_id, decoration_conf)

    # 验证返回格式
```

---

## 四、实施顺序

```
1. Task 1 → 更新 configs/user_config.py (tire_design_width 默认值改为 1000)
2. Task 2 → 创建 rules/rule19.py (中间层实现)
3. Task 3 → 更新 services/postprocessor.py (适配新调用)
4. Task 4 → 创建 tests/unittests/rules/test_rule19.py
5. Task 5 → 更新 tests/unittests/services/test_postprocessor.py
```

---

## 五、参考文档

- [rule13 实现](../../../rules/rule13.py) - 横图打分中间层
- [rule6_1 实现](../../../rules/rule6_1.py) - 图案连续性检测中间层
- [postprocessor 实现](../../../services/postprocessor.py) - 后处理主流程
