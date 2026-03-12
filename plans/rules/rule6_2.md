# 纵图拼接中间层重构计划 (rule6_2)

**创建日期**: 2026-03-11
**状态**: 待实施

---

## 1. 目标

在 `rules/rule6_2.py` 中添加中间层，实现图片文件夹的循环，将流程入口 `services/postprocessor.py::_vertical_stitch` 和算法实现 `algorithms/stitching/vertical_stitch.py::stitch_and_resize` 调用起来。

---

## 2. 架构设计

### 2.1 目标架构

```
postprocessor._vertical_stitch()
    └── rule6_2.process_vertical_stitch()  [新增中间层]
        └── 循环 filters 列表
            └── process_single_dir()
                └── 读取图片 → stitch_and_resize() → 保存
                    └── algorithms/stitching/vertical_stitch.stitch_and_resize()  [纯函数]
```

### 2.2 职责划分

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| `rules/rule6_2.py` | 文件夹循环、IO 操作、结果保存 | 配置 + 路径 | 统计信息 |
| `algorithms/stitching/vertical_stitch.py` | 纯图像处理算法 | PIL.Image | PIL.Image |

---

## 3. 配置体系

### 3.1 配置数据流

```
┌─────────────────────────────────────────────────────────────┐
│ configs/user_config.py                                      │
│ ├── DEFAULT_VERTICAL_STITCH_CONF (模块级常量)               │
│ │   ├── center_vertical: {resolution: [200, 1241]}         │
│ │   ├── side_vertical: {resolution: [400, 1241]}           │
│ │   ├── center_count: 5                                     │
│ │   └── side_count: 5                                       │
│ └── UserConfig.vertical_stitch_conf                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 默认值
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 用户提供的 user_conf (JSON)                                  │
│ └── vertical_stitch_conf (可选，覆盖默认值)                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ services/postprocessor.py                                   │
│ └── _merge_conf_from_complete_config()                      │
│     └── 深度合并：{**DEFAULT, **user_conf}                  │
│         └── vertical_stitch_conf (合并后的配置)              │
│             │
│             ▼
│         _build_vertical_stitch_filters()                    │
│         └── 基于 filter_output_dirs 生成 filters 列表         │
│             │
│             ▼
│         _vertical_stitch()                                  │
│         └── 调用 rule6_2.process_vertical_stitch()          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ rules/rule6_2.py                                            │
│ └── process_vertical_stitch()                               │
│     └── 遍历 conf.filters，调用 process_single_dir()         │
│         └── 读取图片 → stitch_and_resize() → 保存           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ algorithms/stitching/vertical_stitch.py                     │
│ └── stitch_and_resize(image, stitch_count, target_size)     │
│     └── 纯函数：PIL.Image → PIL.Image                       │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 默认配置结构

```python
# configs/user_config.py
DEFAULT_VERTICAL_STITCH_CONF = {
    "center_vertical": {"resolution": [200, 1241]},
    "side_vertical": {"resolution": [400, 1241]},
    "center_count": 5,
    "side_count": 5,
}
```

### 3.3 配置合并逻辑

```python
# 默认配置
{
    "center_vertical": {"resolution": [200, 1241]},
    "side_vertical": {"resolution": [400, 1241]},
    "center_count": 5,
    "side_count": 5,
}

# 用户配置 (user_conf)
{
    "vertical_stitch_conf": {
        "center_vertical": {"resolution": [250, 1300]},  # 覆盖
        "center_count": 6  # 覆盖
    }
}

# 合并后 (merged_conf['vertical_stitch_conf'])
{
    "center_vertical": {"resolution": [250, 1300]},  # 用户覆盖
    "side_vertical": {"resolution": [400, 1241]},    # 默认值
    "center_count": 6,                                # 用户覆盖
    "side_count": 5                                   # 默认值
}

# filters 列表
[
    {"dir": "center_filter", "stitch_count": 6, "resolution": [250, 1300]},
    {"dir": "side_filter", "stitch_count": 5, "resolution": [400, 1241]}
]
```

---

## 4. 实施步骤

### Step 1: 修改 `configs/user_config.py`

**添加模块级常量**（在文件顶部，import 之后）：

```python
# ========== 模块级常量：默认配置 ==========

# 纵图拼接默认配置
DEFAULT_VERTICAL_STITCH_CONF = {
    "center_vertical": {"resolution": [200, 1241]},
    "side_vertical": {"resolution": [400, 1241]},
    "center_count": 5,
    "side_count": 5,
}
```

**在 `UserConfig` 数据类中添加字段**：

```python
@dataclass
class UserConfig:
    # ... 现有字段 ...

    # ========== 纵图拼接参数 ==========
    # 纵图拼接配置（默认值来自 DEFAULT_VERTICAL_STITCH_CONF）
    vertical_stitch_conf: Dict[str, Any] = field(default_factory=dict)
```

**在 `to_dict()` 方法中添加**：

```python
def to_dict(self) -> Dict[str, Any]:
    return {
        # ... 现有字段 ...
        'vertical_stitch_conf': self.vertical_stitch_conf,
    }
```

---

### Step 2: 创建 `rules/rule6_2.py`

```python
# -*- coding: utf-8 -*-
"""
rule6_2: 纵图拼接中间层

功能:
- 接收 postprocessor 的调用
- 循环 filter 目录中的所有图片
- 调用 stitch_and_resize() 进行处理
- 保存结果到输出目录

目录关系:
- 输入：.results/task_id_{task_id}/{filter_dir}/
- 输出：.results/task_id_{task_id}/{base_type}_vertical/
  (center_filter → center_vertical, side_filter → side_vertical)

注意:
- 本模块只负责遍历 conf.filters 列表，不关心列表来源
- 配置校验和 filters 构建在 postprocessor.py 中完成
"""

from pathlib import Path
from typing import Dict, List, Tuple, Any
from PIL import Image
import os

from algorithms.stitching.vertical_stitch import stitch_and_resize
from utils.logger import get_logger

logger = get_logger("rule6_2")


# ========== 主入口函数 ==========

def process_vertical_stitch(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    纵图拼接主入口

    参数:
        task_id: 任务 ID
        conf: 配置字典
            - base_path: 基础路径（默认 ".results"）
            - filters: filter 配置列表（由 postprocessor.py 构建）
                - dir: 目录名（如 "center_filter"）
                - stitch_count: 拼接次数
                - resolution: 目标分辨率 [width, height]
            - output_dir_suffix: 输出目录后缀（默认 "_vertical"）

    返回:
        (True, {"task_id": ..., "directories": {...}, "summary": {...}})
        或 (False, {"err_msg": ..., "task_id": ...})
    """
    # Step 1: 配置校验
    filters = conf.get("filters", [])

    if not filters:
        err_msg = "纵图拼接配置错误：filters 不能为空"
        logger.error(err_msg)
        return False, {
            "err_msg": err_msg,
            "task_id": task_id
        }

    # Step 2: 获取基础路径（默认 ".results"）
    base_path = conf.get("base_path", ".results")

    # Step 3: 构建任务目录
    task_dir = Path(base_path) / f"task_id_{task_id}"

    # Step 4: 循环处理每个 filter 目录
    dir_stats = {}
    for filter_config in filters:
        filter_dir = filter_config.get("dir")
        if not filter_dir:
            logger.warning(f"filter_config 缺少 dir 字段，跳过：{filter_config}")
            continue

        # 获取该 filter 的配置参数
        stitch_count = filter_config.get("stitch_count")
        resolution = filter_config.get("resolution")

        if stitch_count is None or resolution is None:
            err_msg = f"filter_config 缺少必需字段 (stitch_count, resolution): {filter_config}"
            logger.error(err_msg)
            # 这个 filter 配置无效，但继续处理其他 filter
            dir_stats[filter_dir] = {
                "total_count": 0,
                "processed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "images": {},
                "err_msg": err_msg
            }
            continue

        resolution = tuple(resolution)

        # 构建输入输出路径
        input_dir = task_dir / filter_dir

        # 输出目录命名：center_filter → center_vertical
        base_type = filter_dir.replace('_filter', '')
        output_dir_suffix = conf.get("output_dir_suffix", "_vertical")
        output_dir = task_dir / f"{base_type}{output_dir_suffix}"

        # 检查输入目录是否存在
        if not input_dir.exists():
            logger.warning(f"输入目录不存在，跳过：{input_dir}")
            dir_stats[filter_dir] = {
                "total_count": 0,
                "processed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "images": {}
            }
            continue

        # 调用单目录处理函数
        flag, stats = process_single_dir(
            input_dir=input_dir,
            output_dir=output_dir,
            stitch_count=stitch_count,
            target_size=resolution,
            task_id=task_id,
            filter_dir=filter_dir
        )

        if not flag:
            # 单目录失败，记录错误但继续处理其他目录
            logger.error(f"处理目录 {filter_dir} 失败：{stats.get('err_msg', '未知错误')}")
            dir_stats[filter_dir] = {
                "total_count": 0,
                "processed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "images": {},
                "err_msg": stats.get("err_msg", "未知错误")
            }
            continue

        dir_stats[filter_dir] = stats

    # Step 5: 聚合统计
    summary = _aggregate_summary(dir_stats)

    return True, {
        "task_id": task_id,
        "directories": dir_stats,
        "summary": summary
    }


def process_single_dir(
    input_dir: Path,
    output_dir: Path,
    stitch_count: int,
    target_size: tuple,
    task_id: str,
    filter_dir: str
) -> Tuple[bool, dict]:
    """
    处理单个 filter 目录

    参数:
        input_dir: 输入目录
        output_dir: 输出目录
        stitch_count: 拼接次数
        target_size: 目标尺寸 (width, height)
        task_id: 任务 ID
        filter_dir: 目录名

    返回:
        (True, 统计字典) 或 (False, {"err_msg": ...})
    """
    try:
        # Step 1: 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"开始处理目录 {filter_dir}, 输出到 {output_dir}")

        # Step 2: 获取图片列表
        image_files = _get_image_files(input_dir)

        if not image_files:
            logger.warning(f"输入目录为空：{input_dir}")
            return True, {
                "total_count": 0,
                "processed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "images": {}
            }

        # Step 3: 统计信息
        stats = {
            "total_count": len(image_files),
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "images": {}
        }

        # Step 4: 循环处理每张图片
        for image_path in image_files:
            try:
                # 读取图片
                img = Image.open(image_path)

                # 调用算法函数（输入输出都是 PIL.Image）
                result_img = stitch_and_resize(
                    image=img,
                    stitch_count=stitch_count,
                    target_size=target_size
                )

                # 保存结果
                output_path = output_dir / image_path.name
                result_img.save(output_path, "PNG")

                # 记录成功
                stats["success_count"] += 1
                stats["processed_count"] += 1
                stats["images"][image_path.name] = {
                    "status": "success",
                    "output_path": str(output_path)
                }
                logger.debug(f"成功处理图片：{image_path.name}")

            except Exception as e:
                # 单张图片失败，跳过继续下一张
                stats["failed_count"] += 1
                stats["processed_count"] += 1
                stats["images"][image_path.name] = {
                    "status": "failed",
                    "error": str(e)
                }
                logger.error(f"处理图片失败 {image_path.name}: {str(e)}")

        return True, stats

    except Exception as e:
        # 目录级别错误
        logger.error(f"处理目录 {filter_dir} 时发生错误：{str(e)}")
        return False, {"err_msg": str(e)}


# ========== 辅助函数 ==========

def _get_image_files(dir_path: Path) -> List[Path]:
    """
    获取目录内所有图片文件，按文件名排序
    """
    extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    image_files = []
    for ext in extensions:
        image_files.extend(dir_path.glob(f"*{ext}"))
    return sorted(image_files, key=lambda x: x.name)


def _aggregate_summary(dir_stats: Dict[str, dict]) -> dict:
    """
    聚合各目录统计
    """
    return {
        "total_images": sum(s.get("total_count", 0) for s in dir_stats.values()),
        "total_processed": sum(s.get("processed_count", 0) for s in dir_stats.values()),
        "total_success": sum(s.get("success_count", 0) for s in dir_stats.values()),
        "total_failed": sum(s.get("failed_count", 0) for s in dir_stats.values()),
        "total_skipped": sum(s.get("skipped_count", 0) for s in dir_stats.values())
    }
```

---

### Step 3: 重构 `algorithms/stitching/vertical_stitch.py`

```python
# -*- coding: utf-8 -*-
"""
纵图拼接算法模块

提供纯图像处理函数，输入输出都是 PIL.Image 对象。
"""

from PIL import Image
from typing import Tuple


def stitch_and_resize(
    image: Image.Image,
    stitch_count: int,
    target_size: Tuple[int, int]
) -> Image.Image:
    """
    纵向拼接并调整分辨率

    Args:
        image: 输入 PIL.Image 对象
        stitch_count: 拼接次数（将图片纵向复制拼接的次数）
        target_size: 目标尺寸 (width, height)

    Returns:
        Image.Image: 处理后的 PIL.Image 对象

    Raises:
        ValueError: 当参数无效时
    """
    # 参数校验
    if stitch_count < 1:
        raise ValueError(f"stitch_count 必须 >= 1, 当前为 {stitch_count}")

    if not isinstance(target_size, (tuple, list)) or len(target_size) != 2:
        raise ValueError(f"target_size 必须是 (width, height) 格式，当前为 {target_size}")

    # 获取原始图片尺寸
    img_width, img_height = image.size

    # 计算拼接后的尺寸
    stitched_width = img_width
    stitched_height = img_height * stitch_count

    # 创建拼接画布并纵向拼接
    stitched = Image.new("RGB", (stitched_width, stitched_height))
    for i in range(stitch_count):
        stitched.paste(image, (0, i * img_height))

    # 调整尺寸到目标分辨率
    resized = stitched.resize(target_size, Image.LANCZOS)

    return resized
```

---

### Step 4: 修改 `services/postprocessor.py`

**在文件顶部添加导入**（如果需要）：

```python
from configs.user_config import DEFAULT_VERTICAL_STITCH_CONF
```

**添加辅助函数**（在 `_vertical_stitch` 之前）：

```python
def _build_vertical_stitch_filters(vertical_stitch_conf: dict) -> list:
    """
    基于 filter_output_dirs 构建纵图拼接 filters 列表

    Args:
        vertical_stitch_conf: 纵图拼接配置（已合并默认值）
            - center_vertical.resolution: center 方向分辨率
            - side_vertical.resolution: side 方向分辨率
            - center_count: center 方向拼接数量
            - side_count: side 方向拼接数量

    Returns:
        list: filters 列表

    Raises:
        ValueError: 如果配置缺失
    """
    from configs.base_config import SystemConfig

    # 获取 filter_output_dirs（和小图筛选使用同一个配置）
    system_config = SystemConfig()
    filter_output_dirs = system_config.filter_output_dirs

    # 配置校验：不能为空
    if not vertical_stitch_conf:
        raise ValueError("vertical_stitch_conf 不能为空")

    # 遍历 filter_output_dirs，生成 filters
    filters = []
    for filter_dir in filter_output_dirs:
        # 从 filter_dir 提取 base_type: center_filter → center, side_filter → side
        base_type = filter_dir.replace('_filter', '')

        # 从配置中获取该方向的参数
        vertical_key = f"{base_type}_vertical"
        count_key = f"{base_type}_count"

        # 获取分辨率 - 缺少则报错
        vertical_conf = vertical_stitch_conf.get(vertical_key, {})
        resolution = vertical_conf.get("resolution")

        if resolution is None:
            raise ValueError(f"配置缺少 {vertical_key}.resolution")

        # 获取拼接数量 - 缺少则报错
        stitch_count = vertical_stitch_conf.get(count_key)

        if stitch_count is None:
            raise ValueError(f"配置缺少 {count_key}")

        filters.append({
            "dir": filter_dir,
            "stitch_count": stitch_count,
            "resolution": resolution
        })

    return filters
```

**修改 `_merge_conf_from_complete_config` 函数**：

```python
def _merge_conf_from_complete_config(task_id: str, user_conf: dict) -> dict:
    """
    从 CompleteConfig 实例化合并配置

    Args:
        task_id: 任务 ID（用于日志或错误信息）
        user_conf: 用户配置字典

    Returns:
        dict: 合并后的配置字典
    """
    from configs import CompleteConfig
    from configs.user_config import DEFAULT_VERTICAL_STITCH_CONF

    # 实例化 CompleteConfig 获取基础配置
    complete_config = CompleteConfig()
    base_conf = complete_config.to_legacy_dict()

    # 用用户配置覆盖同名项
    merged_conf = {**base_conf, **user_conf}

    # 特殊处理 vertical_stitch_conf：深度合并
    # 用户配置覆盖默认值，但未提供的字段保留默认值
    default_vertical_conf = DEFAULT_VERTICAL_STITCH_CONF
    user_vertical_conf = user_conf.get('vertical_stitch_conf', {})

    # 深度合并：用户配置覆盖默认值
    merged_vertical_conf = {**default_vertical_conf, **user_vertical_conf}
    merged_conf['vertical_stitch_conf'] = merged_vertical_conf

    return merged_conf
```

**修改 `_vertical_stitch` 函数**：

```python
def _vertical_stitch(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    纵图拼接阶段

    Args:
        task_id: 任务 ID
        conf: 配置字典
            - vertical_stitch_conf: 纵图拼接配置（已合并默认值）

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from rules.rule6_2 import process_vertical_stitch

    # 从 conf 中获取 vertical_stitch_conf
    vertical_stitch_conf = conf.get("vertical_stitch_conf", {})

    # 配置校验：不能为空
    if not vertical_stitch_conf:
        return False, {
            "err_msg": "vertical_stitch_conf 不能为空",
            "task_id": task_id
        }

    # 构建 filters 列表（基于 filter_output_dirs）
    try:
        filters = _build_vertical_stitch_filters(vertical_stitch_conf)
    except ValueError as e:
        return False, {
            "err_msg": str(e),
            "task_id": task_id
        }

    # 构建完整的配置传递给 rule6_2
    vertical_stitch_full_conf = {
        "base_path": ".results",
        "filters": filters,
        "output_dir_suffix": "_vertical",
    }

    return process_vertical_stitch(task_id, vertical_stitch_full_conf)
```

---

## 5. 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `configs/user_config.py` | 修改 | 添加 `DEFAULT_VERTICAL_STITCH_CONF` 常量和 `vertical_stitch_conf` 字段 |
| `rules/rule6_2.py` | 新建 | 纵图拼接中间层 |
| `algorithms/stitching/vertical_stitch.py` | 重构 | 删除类，保留纯函数 |
| `services/postprocessor.py` | 修改 | 添加合并逻辑、`_build_vertical_stitch_filters()`、修改 `_vertical_stitch()` |

---

## 6. 错误处理粒度

| 场景 | 处理方式 |
|------|----------|
| `vertical_stitch_conf` 为空 | 报错，返回 `(False, {...})` |
| 缺少 `center_vertical.resolution` | 报错，返回 `(False, {...})` |
| 缺少 `center_count` | 报错，返回 `(False, {...})` |
| 输入目录不存在 | 跳过该目录，记录警告，继续处理其他目录 |
| 单张图片处理失败 | 跳过该图片，记录错误，继续处理下一张 |

---

## 7. 返回格式（参考 rule6_1）

### 成功时

```python
(True, {
    "task_id": "123",
    "directories": {
        "center_filter": {
            "total_count": 10,
            "processed_count": 10,
            "success_count": 9,
            "failed_count": 1,
            "skipped_count": 0,
            "images": {
                "img1.png": {"status": "success", "output_path": "..."},
                "img2.png": {"status": "failed", "error": "..."}
            }
        },
        "side_filter": {...}
    },
    "summary": {
        "total_images": 20,
        "total_processed": 20,
        "total_success": 18,
        "total_failed": 2,
        "total_skipped": 0
    }
})
```

### 失败时

```python
(False, {
    "err_msg": "配置错误：filters 不能为空",
    "task_id": "123"
})
```

---

## 8. 设计原则

1. **配置从 conf 拿，不能代码里写**：所有配置参数都从 `conf` 字典获取
2. **filters 基于 filter_output_dirs 生成**：与小图筛选使用同一个源配置，避免重复输入
3. **日志放在 rule6_2 层**：`stitch_and_resize` 是纯函数，不负责日志
4. **错误处理分层**：
   - 配置错误 → 立即返回失败
   - 目录级别错误 → 跳过该目录，继续处理其他
   - 图片级别错误 → 跳过该图片，继续处理下一张
5. **输入输出是图片对象**：`stitch_and_resize` 接收和返回都是 `PIL.Image`，不负责文件 IO

---

## 9. 备注

- 本计划已确认，待实施
- 实施时严格按照本计划执行，不要改动其他文件
- 配置合并逻辑只在 `_merge_conf_from_complete_config()` 中处理
