# -*- coding: utf-8 -*-

"""
纵图拼接类

实现多个输入目录的纵向图片拼接处理，包括：
- 图片纵向拼接
- 分辨率调整
- 批量处理

# Copyright © 2026 云端辉鸿. All rights reserved.
# Author: 桂禹 <guiyu@cloudhuihong.com>
# AI Assistant: ClaudeCode (Claude Sonnet 4)
"""

from pathlib import Path
import shutil
from PIL import Image


class VerticalStitch:
    """纵图拼接处理类"""

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
