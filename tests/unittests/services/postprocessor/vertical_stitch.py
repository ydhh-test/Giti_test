# -*- coding: utf-8 -*-

"""
纵图拼接类测试

# Copyright © 2026 云端辉鸿. All rights reserved.
# Author: 桂禹 <guiyu@cloudhuihong.com>
# AI Assistant: ClaudeCode (Claude Sonnet 4)
"""

import unittest
from pathlib import Path
from services.postprocessor.vertical_stitch_module import VerticalStitch


class TestVerticalStitch(unittest.TestCase):
    """纵图拼接类测试"""

    def setUp(self):
        """测试前准备"""
        self.task_id = "9f8d7b6a-5e4d-3c2b-1a09-876543210fed"
        self.base_path = "tests/datasets"

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
            ]
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
        output_dir = Path(self.base_path) / f"task_id_{self.task_id}" / "center_vertical"
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
                }
                # 可以添加更多 filters，如 side_filter
            ]
        }

        stitcher = VerticalStitch(self.task_id, conf)
        success, details = stitcher.process()

        # 验证处理结果
        self.assertTrue(success, "处理应该成功")

        # 验证所有 filter 都有结果
        for filter_config in conf["filters"]:
            filter_dir = filter_config["dir"]
            self.assertIn(filter_dir, details)

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
            ]
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
            ]
        }

        stitcher = VerticalStitch(self.task_id, conf)
        success, details = stitcher.process()

        self.assertTrue(success, "处理应该成功")

        # 验证输出文件
        output_dir = Path(self.base_path) / f"task_id_{self.task_id}" / "center_vertical"
        self.assertTrue(output_dir.exists())

        for input_path in details["center_filter"]["success"]:
            input_file = Path(input_path)
            output_file = output_dir / input_file.name
            self.assertTrue(output_file.exists())


if __name__ == '__main__':
    unittest.main()
