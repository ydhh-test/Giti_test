# rule6_1: 图案连续性检测中间层实现计划

**创建日期**: 2026-03-11
**状态**: 计划阶段

---

## 一、整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│ services/postprocessor.py::_small_image_filter                          │
│                                                                          │
│  Step 1: 从 SystemConfig 获取 inf_output_dirs 和 filter_output_dirs       │
│  Step 2: 复制图片 inf → filter (按位置对应)                               │
│  Step 3: 调用 rules/rule6_1.py::process_pattern_continuity()             │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ rules/rule6_1.py::process_pattern_continuity()                          │
│                                                                          │
│  按 filter_output_dirs 循环调用 process_pattern_continuity_single_dir()  │
│  聚合各目录统计结果                                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ rules/rule6_1.py::process_pattern_continuity_single_dir()               │
│                                                                          │
│  循环目录内每张图片:                                                      │
│    - 读取图片 → 转灰度 → 调用 detect_pattern_continuity()                │
│    - is_continuous=False → 删除图片                                       │
│    - visualize=True → 保存可视化到 rule6_1/{base_type}/                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ algorithms/detection/pattern_continuity.py::detect_pattern_continuity() │
│                                                                          │
│  图案连续性检测算法，返回 (score, details)                                │
│  details['is_continuous'] = True/False                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 二、文件结构

```
项目根目录/
├── configs/
│   ├── base_config.py                # 添加 SystemConfig 配置
│   └── ...
├── rules/
│   ├── __init__.py
│   ├── rule6_1.py                    # 新建：图案连续性检测中间层
│   └── scoring/
│       └── ...
├── services/
│   └── postprocessor.py              # 修改 _small_image_filter 函数
├── tests/
│   ├── datasets/
│   │   └── task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/
│   │       ├── center_inf/           # 测试数据源
│   │       └── side_inf/             # 测试数据源
│   └── unittests/
│       └── rules/
│           └── test_rule6_1.py       # 单元测试
└── .results/                         # 运行时生成
    └── task_id_{task_id}/
        ├── center_inf/
        ├── side_inf/
        ├── center_filter/            # 复制后并检测的目录
        ├── side_filter/
        └── rule6_1/                  # 可视化输出
            ├── center/
            └── side/
```

---

## 三、实施步骤

### Step 1: 更新 `configs/base_config.py::SystemConfig`

**添加配置**:

```python
@dataclass
class SystemConfig:
    """系统配置"""

    # 图片目录配置
    inf_output_dirs: List[str] = field(default_factory=lambda: ["center_inf", "side_inf"])
    filter_output_dirs: List[str] = field(default_factory=lambda: ["center_filter", "side_filter"])
```

**说明**:
- `inf_output_dirs`: 原始图片目录列表
- `filter_output_dirs`: 筛选目录列表
- 按位置一一对应：`center_inf → center_filter`, `side_inf → side_filter`

---

### Step 2: 创建 `rules/rule6_1.py`

**模块结构**:

```python
# -*- coding: utf-8 -*-
"""
rule6_1: 图案连续性检测中间层

功能:
- 接收 postprocessor 的调用
- 循环 filter 目录中的所有图片
- 调用 detect_pattern_continuity() 进行图案连续性检测
- 删除不连续的图片
- 保存可视化结果

目录关系:
- 输入：.results/task_id_{task_id}/{filter_dir}/
- 可视化输出：.results/task_id_{task_id}/rule6_1/{base_type}/
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
import shutil
import os
import cv2

from utils.logger import get_logger

logger = get_logger("rule6_1")


def process_pattern_continuity(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    图案连续性检测主入口

    参数:
        task_id: 任务 ID
        conf: 配置字典
            - filter_output_dirs: filter 目录列表 (可选)
            - pattern_continuity_conf: 算法配置
            - visualize: 是否生成可视化
            - output_base_dir: 输出基础目录

    返回:
        (True, 详细统计字典) 或 (False, 错误信息)
    """
    pass


def process_pattern_continuity_single_dir(
    dir_path: Path,
    filter_dir: str,
    task_id: str,
    conf: dict
) -> Tuple[bool, dict]:
    """
    对单个 filter 目录进行图案连续性检测

    参数:
        dir_path: 目录路径
        filter_dir: 目录名 (如 "center_filter")
        task_id: 任务 ID
        conf: 配置字典

    返回:
        (True, 单目录统计) 或 (False, 错误信息)
    """
    pass


# ========== 辅助函数 ==========

def _get_image_files(dir_path: Path) -> List[Path]:
    """获取目录内所有图片文件，按文件名排序"""
    pass


def _copy_images(src_dir: Path, dst_dir: Path) -> None:
    """复制图片文件"""
    pass


def _aggregate_summary(dir_stats: Dict[str, dict]) -> dict:
    """聚合各目录统计"""
    pass


def _build_vis_output_dir(task_id: str, filter_dir: str) -> Path:
    """构建可视化输出目录路径"""
    # .results/task_id_{task_id}/rule6_1/{base_type}/
    # base_type = center_filter → center
    pass
```

---

### Step 3: 更新 `services/postprocessor.py::_small_image_filter`

**修改内容**:

```python
def _small_image_filter(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    小图筛选阶段

    流程:
    1. 从 SystemConfig 获取 inf_output_dirs 和 filter_output_dirs
    2. 复制图片 inf → filter
    3. 调用 rule6_1::process_pattern_continuity()
    4. 返回结果
    """
    from configs.base_config import SystemConfig
    from rules.rule6_1 import process_pattern_continuity
    from pathlib import Path
    import shutil

    # 获取系统配置
    system_config = SystemConfig()
    inf_output_dirs = system_config.inf_output_dirs
    filter_output_dirs = system_config.filter_output_dirs

    # 构建基础路径
    base_path = Path(".results") / f"task_id_{task_id}"

    # Step 1: 复制图片 (inf → filter)
    for inf_dir, filter_dir in zip(inf_output_dirs, filter_output_dirs):
        src_dir = base_path / inf_dir
        dst_dir = base_path / filter_dir

        if src_dir.exists():
            _copy_images(src_dir, dst_dir)
        else:
            logger.warning(f"源目录不存在，跳过：{src_dir}")

    # Step 2: 调用图案连续性检测
    flag, details = process_pattern_continuity(task_id, conf)

    if not flag:
        return False, {
            "err_msg": details.get("err_msg", "图案连续性检测失败"),
            "task_id": task_id,
            "failed_stage": "pattern_continuity"
        }

    # 返回结果
    summary = details.get("summary", {})
    return True, {
        "task_id": task_id,
        "pattern_continuity_stats": details,
        "image_gen_number": summary.get("total_kept", 0),
        "total_deleted": summary.get("total_deleted", 0)
    }


def _copy_images(src_dir: Path, dst_dir: Path) -> None:
    """辅助函数：复制图片"""
    if not src_dir.exists():
        return

    dst_dir.mkdir(parents=True, exist_ok=True)

    extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    for ext in extensions:
        for img_file in src_dir.glob(f"*{ext}"):
            shutil.copy2(str(img_file), str(dst_dir / img_file.name))
```

---

### Step 4: 实现 `rules/rule6_1.py` 详细设计

#### 4.1 `process_pattern_continuity()` 实现

```python
def process_pattern_continuity(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    图案连续性检测主入口

    流程:
    1. 获取 filter_output_dirs
    2. 构建基础路径
    3. 循环调用 process_pattern_continuity_single_dir()
    4. 聚合统计结果
    """
    from configs.base_config import SystemConfig

    # 获取 filter 目录列表
    system_config = SystemConfig()
    filter_output_dirs = conf.get(
        'filter_output_dirs',
        system_config.filter_output_dirs
    )

    # 构建基础路径
    base_path = Path(".results") / f"task_id_{task_id}"

    # 按目录循环处理
    dir_stats = {}
    for filter_dir in filter_output_dirs:
        dir_path = base_path / filter_dir

        # 检查目录是否存在
        if not dir_path.exists():
            logger.warning(f"目录不存在，跳过：{dir_path}")
            dir_stats[filter_dir] = {
                "total_count": 0,
                "kept_count": 0,
                "deleted_count": 0,
                "total_score": 0,
                "images": {}
            }
            continue

        # 调用单目录处理函数
        flag, stats = process_pattern_continuity_single_dir(
            dir_path=dir_path,
            filter_dir=filter_dir,
            task_id=task_id,
            conf=conf
        )

        if not flag:
            return False, {
                "err_msg": f"处理目录 {filter_dir} 失败：{stats.get('err_msg', '未知错误')}",
                "task_id": task_id
            }

        dir_stats[filter_dir] = stats

    # 聚合统计
    summary = _aggregate_summary(dir_stats)

    return True, {
        "task_id": task_id,
        "directories": dir_stats,
        "summary": summary
    }
```

#### 4.2 `process_pattern_continuity_single_dir()` 实现

```python
def process_pattern_continuity_single_dir(
    dir_path: Path,
    filter_dir: str,
    task_id: str,
    conf: dict
) -> Tuple[bool, dict]:
    """
    对单个 filter 目录进行图案连续性检测

    流程:
    1. 获取图片列表
    2. 构建可视化输出目录
    3. 循环处理每张图片
    4. 调用算法 → 判断连续性 → 删除或保留
    """
    from algorithms.detection.pattern_continuity import detect_pattern_continuity

    # 获取图片列表
    image_files = _get_image_files(dir_path)

    # 获取配置
    pattern_continuity_conf = conf.get('pattern_continuity_conf', {})
    visualize = conf.get('visualize', True)

    # 构建可视化输出目录
    # .results/task_id_{task_id}/rule6_1/center/ (center_filter → center)
    vis_output_dir = _build_vis_output_dir(task_id, filter_dir)
    if visualize:
        vis_output_dir.mkdir(parents=True, exist_ok=True)

    # 统计信息
    stats = {
        "total_count": len(image_files),
        "kept_count": 0,
        "deleted_count": 0,
        "total_score": 0,
        "images": {}
    }

    # 循环处理每张图片
    for image_id, image_path in enumerate(image_files):
        try:
            # 读取图片
            img = cv2.imread(str(image_path))
            if img is None:
                logger.warning(f"图片读取失败：{image_path}")
                stats["images"][image_path.name] = {
                    "error": "读取失败",
                    "deleted": True
                }
                stats["deleted_count"] += 1
                continue

            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 调用算法
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

            # 记录结果
            stats["images"][image_path.name] = {
                "score": score,
                "is_continuous": is_continuous,
                "image_id": str(image_id)
            }

            if is_continuous:
                # 连续：保留图片
                stats["kept_count"] += 1
                stats["total_score"] += score
                logger.debug(f"图片连续，保留：{image_path.name}, score={score}")
            else:
                # 不连续：删除图片
                os.remove(str(image_path))
                stats["deleted_count"] += 1
                stats["images"][image_path.name]["deleted"] = True
                logger.debug(f"图片不连续，删除：{image_path.name}")

        except Exception as e:
            logger.error(f"处理图片失败 {image_path.name}: {str(e)}")
            stats["images"][image_path.name] = {
                "error": str(e),
                "deleted": True
            }
            stats["deleted_count"] += 1

    return True, stats
```

#### 4.3 辅助函数实现

```python
def _get_image_files(dir_path: Path) -> List[Path]:
    """获取目录内所有图片文件，按文件名排序"""
    extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    image_files = []
    for ext in extensions:
        image_files.extend(dir_path.glob(f"*{ext}"))
    return sorted(image_files, key=lambda x: x.name)


def _copy_images(src_dir: Path, dst_dir: Path) -> None:
    """复制图片文件"""
    if not src_dir.exists():
        return

    dst_dir.mkdir(parents=True, exist_ok=True)

    for img_file in _get_image_files(src_dir):
        shutil.copy2(str(img_file), str(dst_dir / img_file.name))


def _aggregate_summary(dir_stats: Dict[str, dict]) -> dict:
    """聚合各目录统计"""
    return {
        "total_images": sum(s["total_count"] for s in dir_stats.values()),
        "total_kept": sum(s["kept_count"] for s in dir_stats.values()),
        "total_deleted": sum(s["deleted_count"] for s in dir_stats.values()),
        "total_score": sum(s["total_score"] for s in dir_stats.values())
    }


def _build_vis_output_dir(task_id: str, filter_dir: str) -> Path:
    """
    构建可视化输出目录路径

    .results/task_id_{task_id}/rule6_1/{base_type}/
    base_type = center_filter → center
    """
    base_type = filter_dir.replace('_filter', '')
    return Path(".results") / f"task_id_{task_id}" / "rule6_1" / base_type
```

---

## 四、测试计划

### 测试文件：`tests/unittests/rules/test_rule6_1.py`

#### 测试数据结构

```
tests/datasets/
└── task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/
    ├── center_inf/
    │   ├── 0.png
    │   ├── 1.png
    │   ├── 2.png
    │   └── ...
    └── side_inf/
        ├── 0.png
        ├── 1.png
        └── ...
```

#### 预期结果

- **center_filter**: 只有 `2.png` 保留，其他删除
- **side_filter**: 只有 `0.png` 保留，其他删除

#### 测试用例设计

```python
# -*- coding: utf-8 -*-
"""
rule6_1 单元测试
"""

import pytest
import shutil
from pathlib import Path
import uuid

from rules.rule6_1 import (
    process_pattern_continuity,
    process_pattern_continuity_single_dir,
    _get_image_files,
    _copy_images,
    _aggregate_summary,
    _build_vis_output_dir
)


class TestRule6_1:
    """rule6_1 测试类"""

    # 伪造的 UUID
    TEST_TASK_ID = "test_test_rule6_1"

    # 测试数据源
    DATASET_BASE = Path("tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed")

    # 测试输出目录
    TEST_OUTPUT_BASE = Path(".results") / f"task_id_{TEST_TASK_ID}"

    # 预期保留的图片
    EXPECTED_KEPT = {
        "center_filter": ["2.png"],
        "side_filter": ["0.png"]
    }

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """每个测试前后的准备和清理"""
        # 测试前：清理并准备数据
        self._prepare_test_data()

        yield

        # 测试后：清理输出目录
        self._cleanup_test_data()

    def _prepare_test_data(self):
        """准备测试数据"""
        # 清理旧目录
        if self.TEST_OUTPUT_BASE.exists():
            shutil.rmtree(self.TEST_OUTPUT_BASE)

        # 创建目录结构
        self.TEST_OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

        # 复制测试数据 (inf 目录)
        for inf_dir in ["center_inf", "side_inf"]:
            src = self.DATASET_BASE / inf_dir
            dst = self.TEST_OUTPUT_BASE / inf_dir
            if src.exists():
                shutil.copytree(src, dst)

    def _cleanup_test_data(self):
        """清理测试数据"""
        if self.TEST_OUTPUT_BASE.exists():
            shutil.rmtree(self.TEST_OUTPUT_BASE)

    # ========== 辅助函数测试 ==========

    def test_get_image_files(self):
        """测试图片文件获取"""
        center_inf_dir = self.TEST_OUTPUT_BASE / "center_inf"
        image_files = _get_image_files(center_inf_dir)

        assert len(image_files) > 0
        assert all(f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']
                   for f in image_files)
        # 验证排序
        names = [f.name for f in image_files]
        assert names == sorted(names)

    def test_copy_images(self):
        """测试图片复制"""
        src = self.TEST_OUTPUT_BASE / "center_inf"
        dst = self.TEST_OUTPUT_BASE / "center_filter_copy"

        _copy_images(src, dst)

        assert dst.exists()
        src_files = set(f.name for f in _get_image_files(src))
        dst_files = set(f.name for f in _get_image_files(dst))
        assert src_files == dst_files

    def test_aggregate_summary(self):
        """测试统计聚合"""
        dir_stats = {
            "center_filter": {
                "total_count": 5,
                "kept_count": 3,
                "deleted_count": 2,
                "total_score": 30
            },
            "side_filter": {
                "total_count": 4,
                "kept_count": 2,
                "deleted_count": 2,
                "total_score": 20
            }
        }

        summary = _aggregate_summary(dir_stats)

        assert summary["total_images"] == 9
        assert summary["total_kept"] == 5
        assert summary["total_deleted"] == 4
        assert summary["total_score"] == 50

    def test_build_vis_output_dir(self):
        """测试可视化输出目录构建"""
        vis_dir = _build_vis_output_dir(self.TEST_TASK_ID, "center_filter")
        expected = Path(".results") / f"task_id_{self.TEST_TASK_ID}" / "rule6_1" / "center"
        assert vis_dir == expected

    # ========== 主流程测试 ==========

    def test_process_pattern_continuity_single_dir_center(self):
        """测试单目录处理 - center_filter"""
        # 先复制数据到 filter 目录
        src = self.TEST_OUTPUT_BASE / "center_inf"
        dst = self.TEST_OUTPUT_BASE / "center_filter"
        _copy_images(src, dst)

        # 准备配置
        conf = {
            "pattern_continuity_conf": {
                "score": 10,
                "threshold": 200,
                "edge_height": 4,
                "coarse_threshold": 5,
                "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1,
                "connectivity": 4,
            },
            "visualize": True
        }

        # 调用函数
        flag, stats = process_pattern_continuity_single_dir(
            dir_path=dst,
            filter_dir="center_filter",
            task_id=self.TEST_TASK_ID,
            conf=conf
        )

        # 验证结果
        assert flag is True
        assert stats["total_count"] > 0
        assert stats["kept_count"] == 1  # 只有 2.png 保留
        assert stats["deleted_count"] == stats["total_count"] - 1

        # 验证保留的文件
        remaining_files = list(dst.glob("*.png"))
        remaining_names = set(f.name for f in remaining_files)
        assert remaining_names == {"2.png"}

    def test_process_pattern_continuity_single_dir_side(self):
        """测试单目录处理 - side_filter"""
        # 先复制数据到 filter 目录
        src = self.TEST_OUTPUT_BASE / "side_inf"
        dst = self.TEST_OUTPUT_BASE / "side_filter"
        _copy_images(src, dst)

        # 准备配置
        conf = {
            "pattern_continuity_conf": {
                "score": 10,
                "threshold": 200,
                "edge_height": 4,
                "coarse_threshold": 5,
                "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1,
                "connectivity": 4,
            },
            "visualize": True
        }

        # 调用函数
        flag, stats = process_pattern_continuity_single_dir(
            dir_path=dst,
            filter_dir="side_filter",
            task_id=self.TEST_TASK_ID,
            conf=conf
        )

        # 验证结果
        assert flag is True
        assert stats["kept_count"] == 1  # 只有 0.png 保留

        # 验证保留的文件
        remaining_files = list(dst.glob("*.png"))
        remaining_names = set(f.name for f in remaining_files)
        assert remaining_names == {"0.png"}

    def test_process_pattern_continuity_full(self):
        """测试完整流程 - 所有目录"""
        # 先复制数据到 filter 目录
        for inf_dir, filter_dir in [("center_inf", "center_filter"),
                                      ("side_inf", "side_filter")]:
            src = self.TEST_OUTPUT_BASE / inf_dir
            dst = self.TEST_OUTPUT_BASE / filter_dir
            _copy_images(src, dst)

        # 准备配置
        conf = {
            "filter_output_dirs": ["center_filter", "side_filter"],
            "pattern_continuity_conf": {
                "score": 10,
                "threshold": 200,
                "edge_height": 4,
                "coarse_threshold": 5,
                "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1,
                "connectivity": 4,
            },
            "visualize": True
        }

        # 调用函数
        flag, details = process_pattern_continuity(
            task_id=self.TEST_TASK_ID,
            conf=conf
        )

        # 验证结果
        assert flag is True
        assert "directories" in details
        assert "summary" in details

        # 验证统计
        summary = details["summary"]
        assert summary["total_kept"] == 2  # center 2.png + side 0.png
        assert summary["total_deleted"] == summary["total_images"] - 2

        # 验证最终文件
        center_filter = self.TEST_OUTPUT_BASE / "center_filter"
        side_filter = self.TEST_OUTPUT_BASE / "side_filter"

        center_remaining = set(f.name for f in center_filter.glob("*.png"))
        side_remaining = set(f.name for f in side_filter.glob("*.png"))

        assert center_remaining == {"2.png"}
        assert side_remaining == {"0.png"}

        # 验证可视化文件生成
        vis_center = self.TEST_OUTPUT_BASE / "rule6_1" / "center"
        vis_side = self.TEST_OUTPUT_BASE / "rule6_1" / "side"

        assert vis_center.exists()
        assert vis_side.exists()
        assert len(list(vis_center.glob("*.png"))) > 0
        assert len(list(vis_side.glob("*.png"))) > 0
```

---

## 五、配置项汇总

### SystemConfig (configs/base_config.py)

```python
inf_output_dirs: List[str] = ["center_inf", "side_inf"]
filter_output_dirs: List[str] = ["center_filter", "side_filter"]
```

### _small_image_filter 传入 conf

```python
{
    "filter_output_dirs": ["center_filter", "side_filter"],  # 可选
    "pattern_continuity_conf": {
        "score": 10,
        "threshold": 200,
        "edge_height": 4,
        "coarse_threshold": 5,
        "fine_match_distance": 4,
        "coarse_overlap_ratio": 0.67,
        "use_adaptive_threshold": False,
        "adaptive_method": "otsu",
        "min_line_width": 1,
        "connectivity": 4,
        "vis_line_width": 2,
        "vis_font_scale": 0.5,
        "vis_rectangle_height": 3,
        "vis_rectangle_bottom_offset": 4,
    },
    "visualize": True,
    "output_base_dir": ".results"
}
```

---

## 六、返回格式汇总

### process_pattern_continuity_single_dir 返回

```python
(True, {
    "total_count": 5,
    "kept_count": 1,
    "deleted_count": 4,
    "total_score": 10,
    "images": {
        "0.png": {"score": 0, "is_continuous": False, "deleted": True, "image_id": "0"},
        "1.png": {"score": 0, "is_continuous": False, "deleted": True, "image_id": "1"},
        "2.png": {"score": 10, "is_continuous": True, "image_id": "2"},
        ...
    }
})
```

### process_pattern_continuity 返回

```python
(True, {
    "task_id": "test_test_rule6_1",
    "directories": {
        "center_filter": {...},
        "side_filter": {...}
    },
    "summary": {
        "total_images": 9,
        "total_kept": 2,
        "total_deleted": 7,
        "total_score": 20
    }
})
```

### _small_image_filter 返回

```python
(True, {
    "task_id": "xxx-xxx-xxx",
    "pattern_continuity_stats": {...},
    "image_gen_number": 2,
    "total_deleted": 7
})
```

---

## 七、依赖关系

```
rules/rule6_1.py 依赖:
├── configs/base_config::SystemConfig
├── algorithms/detection/pattern_continuity::detect_pattern_continuity
├── utils/logger::get_logger
├── cv2
├── pathlib
├── shutil
└── os
```

---

## 八、边界情况处理

| 场景 | 处理方式 |
|-----|---------|
| inf 目录不存在 | 跳过该目录的复制，继续处理 |
| inf 目录为空 | 复制后 filter 目录为空，单目录处理返回 total_count=0 |
| filter 目录所有图片被删除 | 继续流程，返回 kept_count=0 |
| 图片读取失败 | 记录 error，该图片不计入统计 |
| 算法抛出异常 | 记录 error，该图片标记为删除 |
| 可视化保存失败 | 记录警告，继续处理 |

---

## 九、实施步骤总结

| 步骤 | 文件 | 任务 |
|-----|------|------|
| 1 | configs/base_config.py | 添加 SystemConfig.inf_output_dirs 和 filter_output_dirs |
| 2 | rules/rule6_1.py | 创建中间层模块，实现主入口和辅助函数 |
| 3 | services/postprocessor.py | 修改 _small_image_filter 函数，调用中间层 |
| 4 | tests/unittests/rules/test_rule6_1.py | 编写单元测试，验证功能 |

---

## 十、注意事项

1. **不要执行计划** - 本文档仅为计划阶段，实际实施需等待确认
2. **不要修改其他文件** - 除上述指定文件外，不修改项目其他部分
3. **测试数据** - 使用 tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/ 下的数据
4. **测试清理** - 每次测试前清理 .results/task_id_test_test_rule6_1/ 目录
5. **预期结果** - 最终只有 center_filter/2.png 和 side_filter/0.png 保留
