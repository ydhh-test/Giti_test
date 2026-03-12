# rule1to5 横图拼接中间层实现计划

**创建日期**: 2026-03-11
**状态**: 待实现

---

## 背景

当前 `_horizontal_stitch` 直接实例化 `HorizontalStitch` 类并调用，缺少像 `rule6_1`/`rule6_2` 那样的中间层封装。需要创建 `rules/rule1to5.py` 作为规则 1-5 的模块，并提供与 `rule6_2` 一致的接口。

---

## 目标

1. 创建 `rules/rule1to5.py` 中间层
2. 返回格式与 `rule6_2` 风格一致
3. 记录每张图片的详细信息

---

## 调用链路

```
修改前:
postprocessor::_horizontal_stitch
    ↓ 直接调用
HorizontalStitch.process()

修改后:
postprocessor::_horizontal_stitch
    ↓ 调用
rules/rule1to5::process_horizontal_stitch  ← 新增中间层
    ↓ 调用
HorizontalStitch.process()  ← 增强返回信息
```

---

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `configs/user_config.py` | 新增配置 | 添加 `DEFAULT_HORIZONTAL_STITCH_CONF` |
| `rules/rule1to5.py` | 新建文件 | 横图拼接中间层 |
| `algorithms/stitching/horizontal_stitch.py` | 修改返回 | `HorizontalStitch.process()` 返回每张图片详情 |
| `services/postprocessor.py` | 修改调用 | `_horizontal_stitch()` 调用中间层 |

---

## 实现步骤

### Step 1: `configs/user_config.py` - 添加默认配置

新增 `DEFAULT_HORIZONTAL_STITCH_CONF` 字典，包含：
- `rib_count`: RIB 数量 (4 或 5)
- `symmetry_type`: 对称类型
- `blend_width`: 边缘融合宽度
- `main_groove_width`: 主沟宽度
- `generation.max_per_mode`: 每种模式最大生成数
- 其他 `HorizontalStitch` 所需配置

---

### Step 2: `algorithms/stitching/horizontal_stitch.py` - 增强返回信息

修改 `HorizontalStitch.process()` 返回格式，增加图片列表：

**当前返回:**
```python
{
    "generated_count": 10,
    "symmetry_types": ["asymmetric", "mirror"],
    "average_score": 8.5
}
```

**修改为:**
```python
{
    "generated_count": 10,
    "symmetry_types": ["asymmetric", "mirror"],
    "average_score": 8.5,
    "images": [
        {
            "filename": "sym_0_r1_0_r2_1_r3_2_r4_1_r5_0.png",
            "output_path": "...",
            "symmetry": "asymmetric",
            "score": 9.0
        },
        ...
    ]
}
```

**需要修改的地方:**
- `save_results()` 函数：收集并返回保存的图片信息
- `process()` 方法：聚合图片列表到返回字典

---

### Step 3: `rules/rule1to5.py` - 创建中间层

```python
# -*- coding: utf-8 -*-
"""
rule1to5: 规则 1-5 处理模块

功能:
- 横图拼接中间层
- 接收 postprocessor 的调用
- 调用 HorizontalStitch.process() 进行处理
- 返回与 rule6_2 风格一致的统计信息

目录关系:
- 输入：.results/task_id_{task_id}/center_vertical/
       .results/task_id_{task_id}/side_vertical/
- 输出：.results/task_id_{task_id}/combine_horizontal/
"""

from pathlib import Path
from typing import Dict, Tuple, Any
from algorithms.stitching.horizontal_stitch import HorizontalStitch
from configs.user_config import DEFAULT_HORIZONTAL_STITCH_CONF
from utils.logger import get_logger

logger = get_logger("rule1to5")


def process_horizontal_stitch(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    横图拼接主入口

    参数:
        task_id: 任务 ID
        conf: 配置字典 (扁平配置，已包含 horizontal_stitch 所需所有字段)
            - center_dir: 将被覆盖为 {task_dir}/center_vertical
            - side_dir: 将被覆盖为 {task_dir}/side_vertical
            - output_dir: 将被覆盖为 {task_dir}/combine_horizontal

    返回:
        成功：(True, {
            "task_id": task_id,
            "directories": {
                "combine_horizontal": {
                    "total_count": ...,
                    "processed_count": ...,
                    "success_count": ...,
                    "failed_count": ...,
                    "skipped_count": ...,
                    "images": {
                        "sym_0_*.png": {"status": "success", "output_path": "..."},
                        ...
                    }
                }
            },
            "summary": {...}
        })
        失败：(False, {"err_msg": ..., "task_id": ...})
    """
    try:
        # Step 1: 配置校验
        if not conf:
            err_msg = "横图拼接配置错误：conf 不能为空"
            logger.error(err_msg)
            return False, {"err_msg": err_msg, "task_id": task_id}

        # Step 2: 合并默认配置
        merged_conf = _merge_conf(conf)

        # Step 3: 构建输入输出路径
        base_path = merged_conf.get("base_path", ".results")
        task_dir = Path(base_path) / f"task_id_{task_id}"

        # 覆盖输入输出目录
        merged_conf['center_dir'] = str(task_dir / "center_vertical")
        merged_conf['side_dir'] = str(task_dir / "side_vertical")
        merged_conf['output_dir'] = str(task_dir / "combine_horizontal")

        # Step 4: 调用 HorizontalStitch
        stitcher = HorizontalStitch(task_id, merged_conf)
        flag, result = stitcher.process()

        if not flag:
            err_msg = result.get('error', '横图拼接失败')
            logger.error(f"横图拼接失败：{err_msg}")
            return False, {"err_msg": err_msg, "task_id": task_id}

        # Step 5: 转换为 rule6_2 风格返回
        stats = _build_stats(result)

        return True, {
            "task_id": task_id,
            "directories": {"combine_horizontal": stats},
            "summary": _aggregate_summary(stats)
        }

    except Exception as e:
        logger.error(f"横图拼接异常：{str(e)}")
        return False, {"err_msg": str(e), "task_id": task_id}


def _merge_conf(user_conf: dict) -> dict:
    """合并用户配置与默认配置"""
    return {**DEFAULT_HORIZONTAL_STITCH_CONF, **user_conf}


def _build_stats(result: dict) -> dict:
    """
    将 HorizontalStitch 的返回转换为 rule6_2 风格的 stats 格式
    """
    images_dict = {}
    image_list = result.get('images', [])

    for img_info in image_list:
        filename = img_info.get('filename', 'unknown')
        images_dict[filename] = {
            "status": "success",
            "output_path": img_info.get('output_path', ''),
            "symmetry": img_info.get('symmetry', ''),
            "score": img_info.get('score', 0.0)
        }

    generated_count = len(image_list)

    return {
        "total_count": generated_count,
        "processed_count": generated_count,
        "success_count": generated_count,
        "failed_count": 0,
        "skipped_count": 0,
        "images": images_dict
    }


def _aggregate_summary(stats: dict) -> dict:
    """聚合统计信息（与 rule6_2 风格一致）"""
    return {
        "total_images": stats.get("total_count", 0),
        "total_processed": stats.get("processed_count", 0),
        "total_success": stats.get("success_count", 0),
        "total_failed": stats.get("failed_count", 0),
        "total_skipped": stats.get("skipped_count", 0)
    }
```

---

### Step 4: `services/postprocessor.py` - 修改 `_horizontal_stitch`

```python
def _horizontal_stitch(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    横图拼接阶段

    Args:
        task_id: 任务 ID
        conf: 横图拼接配置 (扁平配置)

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from rules.rule1to5 import process_horizontal_stitch

    # conf 已经是扁平配置，直接传递给中间层
    return process_horizontal_stitch(task_id, conf)
```

---

## 配置传递说明

1. `postprocessor.py` line 158 获取配置:
   ```python
   horizontal_stitch_conf = merged_conf.get("horizontal_stitch_conf", {})
   ```

2. 该配置为扁平格式，直接传递给中间层

3. 中间层 (`rule1to5.py`) 负责:
   - 合并默认配置 (`DEFAULT_HORIZONTAL_STITCH_CONF`)
   - 覆盖输入输出目录路径:
     - `center_dir` → `{task_dir}/center_vertical`
     - `side_dir` → `{task_dir}/side_vertical`
     - `output_dir` → `{task_dir}/combine_horizontal`

---

## 返回格式对比

### HorizontalStitch.process() 返回 (增强后)
```python
{
    "generated_count": 10,
    "symmetry_types": ["asymmetric", "mirror"],
    "average_score": 8.5,
    "images": [
        {"filename": "sym_0_*.png", "output_path": "...", "symmetry": "asymmetric", "score": 9.0},
        ...
    ]
}
```

### rule1to5.process_horizontal_stitch() 返回 (rule6_2 风格)
```python
(True, {
    "task_id": task_id,
    "directories": {
        "combine_horizontal": {
            "total_count": 10,
            "processed_count": 10,
            "success_count": 10,
            "failed_count": 0,
            "skipped_count": 0,
            "images": {
                "sym_0_*.png": {
                    "status": "success",
                    "output_path": "...",
                    "symmetry": "asymmetric",
                    "score": 9.0
                },
                ...
            }
        }
    },
    "summary": {
        "total_images": 10,
        "total_processed": 10,
        "total_success": 10,
        "total_failed": 0,
        "total_skipped": 0
    }
})
```

---

## 目录结构

```
rules/
├── __init__.py
├── rule1to5.py          # 新建：规则 1-5 模块（含横图拼接中间层）
├── rule6_1.py           # 图案连续性检测
└── rule6_2.py           # 纵图拼接
```

---

## 注意事项

1. **不要修改配置结构** - `horizontal_stitch_conf` 保持扁平格式
2. **错误处理** - 直接返回 `(False, {"err_msg": ..., "task_id": ...})`
3. **输出目录创建** - 由 `HorizontalStitch` 内部负责创建
4. **图片详情记录** - 中间层需要记录每张图片的详细信息

---

## 实现检查清单

- [ ] Step 1: 在 `configs/user_config.py` 添加 `DEFAULT_HORIZONTAL_STITCH_CONF`
- [ ] Step 2: 修改 `algorithms/stitching/horizontal_stitch.py` 增强返回信息
  - [ ] 修改 `save_results()` 收集图片信息
  - [ ] 修改 `process()` 返回图片列表
- [ ] Step 3: 创建 `rules/rule1to5.py` 中间层
  - [ ] 实现 `process_horizontal_stitch()`
  - [ ] 实现 `_merge_conf()`
  - [ ] 实现 `_build_stats()`
  - [ ] 实现 `_aggregate_summary()`
- [ ] Step 4: 修改 `services/postprocessor.py::_horizontal_stitch`
  - [ ] 导入 `process_horizontal_stitch`
  - [ ] 修改调用逻辑

---

## 相关文件参考

- `rules/rule6_1.py` - 图案连续性检测中间层 (参考结构)
- `rules/rule6_2.py` - 纵图拼接中间层 (参考结构和返回格式)
- `algorithms/stitching/horizontal_stitch.py` - 横图拼接算法实现
- `algorithms/stitching/vertical_stitch.py` - 纵图拼接算法实现
