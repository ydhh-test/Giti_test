# VerticalStitch 实现方案

## 概述

将 `_vertical_stitch()` 函数改造为 `VerticalStitch` 类，实现对多个输入目录进行纵向拼接处理。

## 配置结构

```python
vertical_stitch_conf = {
    "base_path": "tests/datasets",
    "filters": [
        {
            "dir": "center_filter",
            "stitch_count": 5,
            "resolution": [200, 1241]
        },
        {
            "dir": "side_filter",
            "stitch_count": 6,
            "resolution": [400, 1241]
        }
    ]
}
```

## 类设计

```python
class VerticalStitch:
    def __init__(self, task_id: str, conf: dict):
        """
        初始化纵向拼接类

        Args:
            task_id: 任务ID
            conf: 配置字典，包含 base_path 和 filters
        """
        self.task_id = task_id
        self.conf = conf
        self.base_path = conf["base_path"]
        self.filters = conf["filters"]

    def process(self) -> tuple[bool, dict]:
        """
        主处理流程

        Returns:
            tuple[bool, dict]: (是否成功, 处理详情)
                details 格式:
                {
                    "center_filter": {
                        "success": ["path/to/1.png", ...],
                        "failed": ["path/to/2.png", ...],
                        "skipped": []
                    },
                    "side_filter": {
                        "success": [...],
                        "failed": [...],
                        "skipped": []
                    }
                }
        """
        results = {}
        all_success = True

        for filter_config in self.filters:
            filter_dir = filter_config["dir"]
            result = self._process_filter(filter_config)
            results[filter_dir] = result

            if result["failed"]:
                all_success = False

        return all_success, results

    def _process_filter(self, filter_config: dict) -> dict:
        """
        处理单个 filter 目录

        Args:
            filter_config: 单个 filter 的配置

        Returns:
            dict: 包含 success, failed, skipped 列表
        """
        filter_dir = filter_config["dir"]
        stitch_count = filter_config["stitch_count"]
        resolution = tuple(filter_config["resolution"])

        result = {
            "success": [],
            "failed": [],
            "skipped": []
        }

        # 获取目录路径
        task_dir = self._get_task_dir()
        input_dir = task_dir / filter_dir
        output_dir = task_dir / f"{filter_dir.split('_')[0]}_vertical"

        # 检查输入目录是否存在
        if not input_dir.exists():
            result["skipped"].append(str(input_dir))
            return result

        # 检查是否为空目录
        if not any(input_dir.iterdir()):
            result["skipped"].append(str(input_dir))
            return result

        # 清空并重建输出目录
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 按文件名排序获取图片列表
        image_files = sorted(input_dir.glob("*.png"), key=lambda x: x.name)

        # 逐张处理图片
        for image_path in image_files:
            try:
                success = self._stitch_and_resize(
                    image_path,
                    output_dir / image_path.name,
                    stitch_count,
                    resolution
                )
                if success:
                    result["success"].append(str(image_path))
                else:
                    result["failed"].append(str(image_path))
            except Exception as e:
                result["failed"].append(str(image_path))

        return result

    def _stitch_and_resize(
        self,
        input_path: Path,
        output_path: Path,
        stitch_count: int,
        target_size: tuple
    ) -> bool:
        """
        对单张图片进行纵向拼接和 resize

        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            stitch_count: 拼接次数
            target_size: 目标尺寸 (width, height)

        Returns:
            bool: 是否处理成功
        """
        try:
            # 读取原始图片
            img = Image.open(input_path)
            img_width, img_height = img.size

            # 创建拼接后的图片画布
            stitched_width = img_width
            stitched_height = img_height * stitch_count
            stitched = Image.new("RGB", (stitched_width, stitched_height))

            # 纵向拼接
            for i in range(stitch_count):
                stitched.paste(img, (0, i * img_height))

            # Resize 到目标尺寸
            resized = stitched.resize(target_size, Image.LANCZOS)

            # 保存图片
            resized.save(output_path, "PNG")

            return True

        except Exception as e:
            return False

    def _get_task_dir(self) -> Path:
        """
        获取 task_id 目录路径

        Returns:
            Path: task_id 目录路径
        """
        return Path(self.base_path) / f"task_id_{self.task_id}"
```

## 处理流程

1. **初始化**
   - 接收 task_id 和配置
   - 构建 base_path 和 filters 列表

2. **主处理**
   - 遍历 filters 列表
   - 对每个 filter 调用 `_process_filter()`
   - 收集所有结果
   - 如果有任何失败，返回 False

3. **单 filter 处理**
   - 检查输入目录是否存在（不存在则跳过）
   - 检查目录是否为空（为空则跳过）
   - 清空并重建输出目录
   - 按文件名排序获取图片列表
   - 逐张调用 `_stitch_and_resize()`
   - 记录成功/失败/跳过的图片路径

4. **单张图片处理**
   - 读取原始图片 (128x128)
   - 创建纵向拼接后的画布 (128 x 128*N)
   - 将原图纵向拼接 N 次
   - Resize 到目标尺寸 (width x height)
   - 保存为 PNG 格式
   - 捕获异常，失败返回 False

## 目录结构

### 输入
```
tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/
  ├── center_filter/
  │   ├── 1.png (128x128)
  │   ├── 8.png (128x128)
  │   └── ...
  └── side_filter/
      ├── 1.png (128x128)
      └── ...
```

### 输出
```
tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/
  ├── center_vertical/
  │   ├── 1.png (200x1241)
  │   ├── 8.png (200x1241)
  │   └── ...
  └── side_vertical/
      ├── 1.png (400x1241)
      └── ...
```

## 技术细节

- **图像处理库**: Pillow (PIL)
- **输入输出格式**: PNG
- **原始图片尺寸**: 128x128
- **拼接方式**: 原图纵向拼接 N 次（从上到下）
- **Resize 方法**: Image.LANCZOS（高质量）
- **文件排序**: 按文件名排序
- **输出目录策略**: 每次清空重建

## 错误处理策略

| 场景 | 处理方式 |
|------|----------|
| 输入目录不存在 | 跳过该 filter，记录到 skipped |
| 输入目录为空 | 跳过该 filter，记录到 skipped |
| 输出文件已存在 | 理论上不会发生（清空重建），如果发生则报错 |
| 图片损坏 | 跳过该图片，记录到 failed |
| 图片处理失败 | 捕获异常，记录到 failed |
| 任何图片失败 | 整体结果返回 False |

## 返回值格式

```python
(
    True,  # 是否全部成功
    {
        "center_filter": {
            "success": [
                "tests/datasets/task_id_xxx/center_filter/1.png",
                "tests/datasets/task_id_xxx/center_filter/8.png"
            ],
            "failed": [],
            "skipped": []
        },
        "side_filter": {
            "success": [
                "tests/datasets/task_id_xxx/side_filter/1.png"
            ],
            "failed": [
                "tests/datasets/task_id_xxx/side_filter/corrupted.png"
            ],
            "skipped": []
        }
    }
)
```

## 依赖

```python
from pathlib import Path
import shutil
from PIL import Image
```

## 集成到 postprocessor.py

```python
def _vertical_stitch(task_id: str, conf: dict) -> tuple[bool, dict]:
    """纵图拼接"""
    stitcher = VerticalStitch(task_id, conf)
    return stitcher.process()
```

## 待确认事项

- [x] 配置结构：filters 列表形式，每个 filter 独立配置
- [x] 拼接次数：每个 filter 可配置不同的 stitch_count
- [x] 分辨率：每个 filter 可配置不同的 resolution
- [x] 图像库：使用 Pillow
- [x] 排序方式：按文件名排序
- [x] 输出目录：清空重建
- [x] 错误处理：损坏图片跳过，目录不存在跳过
- [x] 返回详情：记录成功/失败/跳过的图片路径
