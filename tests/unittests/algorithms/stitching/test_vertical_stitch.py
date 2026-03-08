# -*- coding: utf-8 -*-

"""
纵图拼接类测试

# Copyright © 2026. All rights reserved.
# Author: 桂禹
# AI Assistant: ClaudeCode (Claude Sonnet 4)
"""

import unittest
import shutil
from pathlib import Path
from algorithms.stitching.vertical_stitch import VerticalStitch
from utils.logger import setup_logger


class TestVerticalStitch(unittest.TestCase):
    """纵图拼接类测试"""

    def setUp(self):
        """测试前准备"""
        # 新的 task_id
        self.task_id = "ae789b2c-8f45-4a9d-b76e-890c78d56789"
        self.base_path = ".results"

        # 源数据路径
        self.source_task_id = "9f8d7b6a-5e4d-3c2b-1a09-876543210fed"
        self.source_base_path = "tests/datasets"

        # 复制测试数据
        self._setup_test_data()

        # 配置 logger
        self._setup_logger()

    def _setup_test_data(self):
        """复制测试数据到 .results 目录"""
        source_dir = Path(self.source_base_path) / f"task_id_{self.source_task_id}"
        target_dir = Path(self.base_path) / f"task_id_{self.task_id}"

        # 创建目标目录
        target_dir.mkdir(parents=True, exist_ok=True)

        # 复制 center_filter 和 side_filter
        for filter_name in ["center_filter", "side_filter"]:
            src = source_dir / filter_name
            dst = target_dir / filter_name

            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)

    def _setup_logger(self):
        """配置 logger 写入 .logs 目录"""
        log_dir = Path(".logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"test_vertical_stitch_{self.task_id}.log"
        setup_logger("VerticalStitch", level="DEBUG", log_file=str(log_file))

    def test_vertical_stitch_single_filter(self):
        """测试单个 filter 的纵向拼接"""
        conf = {
            "base_path": self.base_path,
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": 5,
                    "resolution": [200, 1241]
                }
            ],
            "vertical_stitch_conf": {
                "output_dir_suffix": "_combine"
            },
            "postprocessor_conf": {
                "supported_image_extensions": [".png"]
            }
        }

        stitcher = VerticalStitch(self.task_id, conf)
        success, details = stitcher.process()

        # 验证处理结果
        self.assertTrue(success, "处理应该成功")

        # 验证结果结构
        self.assertIn("center_filter", details)
        center_result = details["center_filter"]

        # 验证至少有一些成功的图片
        self.assertGreater(len(center_result["success"]), 0,
                         "应该有成功处理的图片")

        # 验证没有失败的图片
        self.assertEqual(len(center_result["failed"]), 0,
                        "不应该有失败的图片")

        # 验证输出目录存在
        output_dir = Path(self.base_path) / f"task_id_{self.task_id}" / "center_combine"
        self.assertTrue(output_dir.exists(),
                       f"输出目录 {output_dir} 应该存在")

        # 验证输出文件存在
        for input_path in center_result["success"]:
            input_file = Path(input_path)
            output_file = output_dir / input_file.name
            self.assertTrue(output_file.exists(),
                          f"输出文件 {output_file} 应该存在")

            # 验证输出文件是 PNG 格式
            self.assertEqual(output_file.suffix, ".png",
                           f"输出文件应该是 PNG 格式")

            # 可以选择验证图片尺寸
            # from PIL import Image
            # img = Image.open(output_file)
            # self.assertEqual(img.size, (200, 1241),
            #                f"图片尺寸应该是 200x1241，但实际是 {img.size}")

    def test_vertical_stitch_multiple_filters(self):
        """测试多个 filters 的纵向拼接"""
        conf = {
            "base_path": self.base_path,
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
            ],
            "vertical_stitch_conf": {
                "output_dir_suffix": "_combine"
            },
            "postprocessor_conf": {
                "supported_image_extensions": [".png"]
            }
        }

        stitcher = VerticalStitch(self.task_id, conf)
        success, details = stitcher.process()

        # 验证处理结果
        self.assertTrue(success, "处理应该成功")

        # 验证所有 filter 都有结果
        for filter_config in conf["filters"]:
            filter_dir = filter_config["dir"]
            self.assertIn(filter_dir, details)

        # 验证输出目录
        center_output = Path(self.base_path) / f"task_id_{self.task_id}" / "center_combine"
        side_output = Path(self.base_path) / f"task_id_{self.task_id}" / "side_combine"

        self.assertTrue(center_output.exists(), "center_combine 目录应该存在")
        self.assertTrue(side_output.exists(), "side_combine 目录应该存在")

        # 验证输出文件
        center_images = list(center_output.glob("*.png"))
        side_images = list(side_output.glob("*.png"))

        self.assertGreater(len(center_images), 0, "center_combine 应该有图片")
        self.assertGreater(len(side_images), 0, "side_combine 应该有图片")

    def test_vertical_stitch_nonexistent_directory(self):
        """测试不存在的目录"""
        conf = {
            "base_path": self.base_path,
            "filters": [
                {
                    "dir": "nonexistent_filter",
                    "stitch_count": 5,
                    "resolution": [200, 1241]
                }
            ],
            "vertical_stitch_conf": {
                "output_dir_suffix": "_combine"
            },
            "postprocessor_conf": {
                "supported_image_extensions": [".png"]
            }
        }

        stitcher = VerticalStitch(self.task_id, conf)
        success, details = stitcher.process()

        # 验证处理结果
        # 目录不存在时应该跳过，但仍返回 True
        self.assertTrue(success, "处理应该成功（跳过不存在的目录）")

        # 验证目录被跳过
        self.assertIn("nonexistent_filter", details)
        self.assertEqual(len(details["nonexistent_filter"]["success"]), 0)
        self.assertEqual(len(details["nonexistent_filter"]["failed"]), 0)
        self.assertEqual(len(details["nonexistent_filter"]["skipped"]), 1)

    def test_vertical_stitch_different_stitch_counts(self):
        """测试不同的拼接次数"""
        # 测试拼接次数为 6
        conf = {
            "base_path": self.base_path,
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": 6,
                    "resolution": [200, 1241]
                }
            ],
            "vertical_stitch_conf": {
                "output_dir_suffix": "_combine"
            },
            "postprocessor_conf": {
                "supported_image_extensions": [".png"]
            }
        }

        stitcher = VerticalStitch(self.task_id, conf)
        success, details = stitcher.process()

        self.assertTrue(success, "处理应该成功")

        # 验证输出文件
        output_dir = Path(self.base_path) / f"task_id_{self.task_id}" / "center_combine"
        self.assertTrue(output_dir.exists())

        for input_path in details["center_filter"]["success"]:
            input_file = Path(input_path)
            output_file = output_dir / input_file.name
            self.assertTrue(output_file.exists())


if __name__ == '__main__':
    unittest.main()
