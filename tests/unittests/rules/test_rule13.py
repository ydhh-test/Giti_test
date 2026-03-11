# -*- coding: utf-8 -*-
"""
rule13 单元测试 - 横图打分中间层
"""

import pytest
import shutil
import cv2
import numpy as np
from pathlib import Path

from rules.rule13 import (
    process_horizontal_image_score,
    process_single_image,
    visualize_score,
    save_score_json,
    _get_image_files,
    _aggregate_summary
)


class TestRule13:
    """rule13 测试类"""

    # 伪造的 Task ID
    TEST_TASK_ID = "test_rule13"

    # 测试输出目录
    TEST_OUTPUT_BASE = Path(".results") / f"task_id_{TEST_TASK_ID}"

    # 测试数据集路径
    DATASET_BASE = Path("tests/datasets/task_id_test_rule13")

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, request):
        """每个测试前的准备"""
        # 检查是否是总的正例测试
        is_full_test = request.function.__name__ == "test_process_horizontal_image_score_full"

        # 总的正例测试不清理，其他测试需要清理
        if not is_full_test:
            self._cleanup_test_data()

        yield

        # 测试后：保留输出目录，不清理（便于手动验证）

    def _cleanup_test_data(self):
        """清理测试数据"""
        if self.TEST_OUTPUT_BASE.exists():
            shutil.rmtree(self.TEST_OUTPUT_BASE)

    def _create_test_image(self, dir_path: Path, filename: str,
                           black_ratio: float = 0.3, gray_ratio: float = 0.2) -> Path:
        """
        创建测试图片

        参数:
            dir_path: 输出目录
            filename: 文件名
            black_ratio: 黑色区域占比 (0-1)
            gray_ratio: 灰色区域占比 (0-1)

        返回:
            图片路径
        """
        dir_path.mkdir(parents=True, exist_ok=True)
        image_path = dir_path / filename

        # 创建 200x200 测试图片
        height, width = 200, 200
        total_pixels = height * width

        # 计算各区域像素数
        black_pixels = int(total_pixels * black_ratio)
        gray_pixels = int(total_pixels * gray_ratio)
        white_pixels = total_pixels - black_pixels - gray_pixels

        # 创建灰度图
        img = np.zeros((height, width), dtype=np.uint8)

        # 填充黑色区域 (0-50)
        img.flat[:black_pixels] = 30

        # 填充灰色区域 (51-200)
        img.flat[black_pixels:black_pixels + gray_pixels] = 120

        # 填充白色区域 (201-255)
        img.flat[black_pixels + gray_pixels:] = 240

        # 保存为 BGR 图片
        img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        cv2.imwrite(str(image_path), img_bgr)

        return image_path

    def _copy_test_data(self) -> int:
        """
        复制测试数据到输出目录

        从 tests/datasets/task_id_test_rule13/combine_horizontal/
        复制到 .results/task_id_test_rule13/combine_horizontal/

        返回:
            复制的图片数量
        """
        src_dir = self.DATASET_BASE / "combine_horizontal"
        dst_dir = self.TEST_OUTPUT_BASE / "combine_horizontal"

        if not src_dir.exists():
            return 0

        # 创建目标目录
        dst_dir.mkdir(parents=True, exist_ok=True)

        # 复制所有图片
        count = 0
        for img_file in src_dir.glob("*.png"):
            shutil.copy2(str(img_file), str(dst_dir / img_file.name))
            count += 1

        return count

    # ========== 辅助函数测试 ==========

    def test_get_image_files(self):
        """测试图片文件获取"""
        # 创建测试目录和图片
        test_dir = self.TEST_OUTPUT_BASE / "test_get_image_files"
        test_dir.mkdir(parents=True, exist_ok=True)

        # 创建多个图片文件
        for name in ["c.png", "a.png", "b.png"]:
            self._create_test_image(test_dir, name)

        # 调用函数
        image_files = _get_image_files(test_dir)

        # 验证结果
        assert len(image_files) == 3
        # 验证排序
        names = [f.name for f in image_files]
        assert names == ["a.png", "b.png", "c.png"]
        # 验证扩展名
        assert all(f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']
                   for f in image_files)

    def test_aggregate_summary(self):
        """测试统计聚合"""
        image_results = [
            {"status": "success", "score": 2, "land_sea_ratio": 30.5},
            {"status": "success", "score": 1, "land_sea_ratio": 25.0},
            {"status": "failed", "error": "读取失败"},
            {"status": "success", "score": 2, "land_sea_ratio": 32.0},
        ]

        summary = _aggregate_summary(image_results)

        assert summary["total_images"] == 4
        assert summary["total_scored"] == 3
        assert summary["total_failed"] == 1
        assert summary["total_score"] == 5  # 2 + 1 + 2

    # ========== 可视化函数测试 ==========

    def test_visualize_score(self):
        """测试可视化输出函数"""
        # 创建测试图片
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        img[:, :] = [120, 120, 120]  # 灰色背景

        # 输出路径
        output_path = self.TEST_OUTPUT_BASE / "test_vis" / "test_visualize.png"

        # 调用函数
        visualize_score(img, score=2, ratio=30.5, output_path=output_path)

        # 验证输出文件存在
        assert output_path.exists()

        # 验证输出图片可以读取
        result_img = cv2.imread(str(output_path))
        assert result_img is not None
        assert result_img.shape == img.shape

    def test_save_score_json(self):
        """测试 JSON 保存函数"""
        # 测试数据
        score_data = {
            "task_id": self.TEST_TASK_ID,
            "image_name": "test.png",
            "image_id": "0",
            "score": 2,
            "land_sea_ratio": 30.5,
            "status": "success",
            "details": {
                "ratio_value": 30.5,
                "target_range": "[28.0%, 35.0%]",
                "black_area": 10000,
                "gray_area": 20000,
                "total_area": 100000
            },
            "vis_path": str(self.TEST_OUTPUT_BASE / "test_vis" / "test.png"),
            "json_path": str(self.TEST_OUTPUT_BASE / "scores" / "rule13" / "test.png.json")
        }

        # 输出路径
        output_path = self.TEST_OUTPUT_BASE / "scores" / "rule13" / "test.png.json"

        # 调用函数
        save_score_json(score_data, output_path)

        # 验证输出文件存在
        assert output_path.exists()

        # 验证 JSON 内容
        import json
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        assert loaded_data["task_id"] == self.TEST_TASK_ID
        assert loaded_data["score"] == 2
        assert loaded_data["land_sea_ratio"] == 30.5

    # ========== 边界情况测试 ==========

    def test_process_horizontal_image_score_nonexistent_dir(self):
        """测试目录不存在的情况"""
        conf = {
            "input_dir": "nonexistent_dir",
            "land_sea_ratio": {
                "target_min": 28.0,
                "target_max": 35.0,
                "margin": 5.0
            },
            "visualize": True,
            "output_base_dir": str(self.TEST_OUTPUT_BASE.parent)
        }

        # 调用函数
        flag, details = process_horizontal_image_score(self.TEST_TASK_ID, conf)

        # 验证结果
        assert flag is True  # 目录不存在不报错，返回空统计
        assert details["summary"]["total_images"] == 0
        assert details["summary"]["total_scored"] == 0

    def test_process_horizontal_image_score_empty_dir(self):
        """测试输入目录为空的情况"""
        # 创建空目录
        empty_dir = self.TEST_OUTPUT_BASE / "empty_combine_horizontal"
        empty_dir.mkdir(parents=True, exist_ok=True)

        conf = {
            "input_dir": "empty_combine_horizontal",
            "land_sea_ratio": {
                "target_min": 28.0,
                "target_max": 35.0,
                "margin": 5.0
            },
            "visualize": True,
            "output_base_dir": str(self.TEST_OUTPUT_BASE.parent)
        }

        # 调用函数
        flag, details = process_horizontal_image_score(self.TEST_TASK_ID, conf)

        # 验证结果
        assert flag is True
        assert details["summary"]["total_images"] == 0
        assert details["summary"]["total_scored"] == 0

    # ========== 单图处理测试 ==========

    def test_process_single_image(self):
        """测试单张图片处理"""
        # 创建测试图片（海陆比约 50%，超出目标范围）
        input_dir = self.TEST_OUTPUT_BASE / "test_single_input"
        image_path = self._create_test_image(
            input_dir,
            "test_single.png",
            black_ratio=0.3,  # 30% 黑色
            gray_ratio=0.2    # 20% 灰色，总计 50%
        )

        conf = {
            "land_sea_ratio": {
                "target_min": 28.0,
                "target_max": 35.0,
                "margin": 5.0
            },
            "visualize": True,
            "output_base_dir": str(self.TEST_OUTPUT_BASE.parent)
        }

        # 调用函数
        flag, result = process_single_image(
            image_path=image_path,
            task_id=self.TEST_TASK_ID,
            conf=conf,
            image_id=0
        )

        # 验证结果
        assert flag is True
        assert result["status"] == "success"
        assert result["image_name"] == "test_single.png"
        assert result["image_id"] == "0"
        assert "score" in result
        assert "land_sea_ratio" in result

        # 50% 海陆比超出目标范围 [28%, 35%] + margin 5%，应该得 0 分
        assert result["score"] == 0
        assert result["land_sea_ratio"] > 35.0

        # 验证可视化文件
        assert Path(result["vis_path"]).exists()

        # 验证 JSON 文件
        assert Path(result["json_path"]).exists()

    # ========== 完整流程测试 ==========

    def test_process_horizontal_image_score_full(self):
        """
        总的正例测试 - 完整的横图打分流程（使用真实测试数据）

        测试场景:
        - 从 tests/datasets/task_id_test_rule13/combine_horizontal/ 复制 3 张图片
        - 执行完整的横图打分流程
        - 验证返回值、评分结果、JSON 文件、可视化文件

        注意：此测试执行后不清理，便于手动验证结果
        """
        # ========== Step 0: 清理旧目录（保证测试环境干净） ==========
        # 注意：测试后不清理，便于手动验证
        self._cleanup_test_data()

        # ========== Step 1: 准备测试数据 - 复制图片 ==========
        copied_count = self._copy_test_data()
        assert copied_count == 3, f"预期复制 3 张图片，实际复制 {copied_count} 张"

        # 验证复制成功
        combine_horizontal_dir = self.TEST_OUTPUT_BASE / "combine_horizontal"
        assert combine_horizontal_dir.exists()
        image_files = list(combine_horizontal_dir.glob("*.png"))
        assert len(image_files) == 3

        # ========== Step 2: 准备配置 ==========
        conf = {
            "input_dir": "combine_horizontal",
            "land_sea_ratio": {
                "target_min": 28.0,
                "target_max": 35.0,
                "margin": 5.0
            },
            "visualize": True,
            "output_base_dir": str(self.TEST_OUTPUT_BASE.parent)
        }

        # ========== Step 3: 调用函数 ==========
        flag, details = process_horizontal_image_score(self.TEST_TASK_ID, conf)

        # ========== Step 4: 验证返回值结构 ==========
        assert flag is True
        assert "task_id" in details
        assert "directories" in details
        assert "summary" in details

        # ========== Step 5: 验证统计信息 ==========
        summary = details["summary"]
        assert summary["total_images"] == 3
        assert summary["total_scored"] == 3
        assert summary["total_failed"] == 0
        assert summary["total_score"] == 3  # 1 + 1 + 1 = 3

        # ========== Step 6: 验证每张图片的评分结果 ==========
        images = details["directories"]["combine_horizontal"]["images"]
        assert len(images) == 3

        # 图片 1: 海陆比 24.72%，得分 1（在 [23%, 28%) 范围内）
        img0 = images["sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png"]
        assert img0["score"] == 1
        assert img0["land_sea_ratio"] == 24.72
        assert img0["status"] == "success"
        assert Path(img0["vis_path"]).exists()
        assert Path(img0["json_path"]).exists()

        # 图片 2: 海陆比 24.36%，得分 1（在 [23%, 28%) 范围内）
        img1 = images["sym_1_r1_0_r2_0_r3_1_r4_0_r5_0.png"]
        assert img1["score"] == 1
        assert img1["land_sea_ratio"] == 24.36
        assert img1["status"] == "success"
        assert Path(img1["vis_path"]).exists()
        assert Path(img1["json_path"]).exists()

        # 图片 3: 海陆比 25.25%，得分 1（在 [23%, 28%) 范围内）
        img2 = images["sym_3_r1_0_r2_0_r3_0_r4_0_r5_0.png"]
        assert img2["score"] == 1
        assert img2["land_sea_ratio"] == 25.25
        assert img2["status"] == "success"
        assert Path(img2["vis_path"]).exists()
        assert Path(img2["json_path"]).exists()

        # ========== Step 7: 验证 JSON 文件存在性 ==========
        scores_dir = self.TEST_OUTPUT_BASE / "scores" / "rule13"
        assert scores_dir.exists()
        json_files = list(scores_dir.glob("*.json"))
        assert len(json_files) == 3

        # 验证每个 JSON 文件存在
        for filename, img_data in images.items():
            json_path = Path(img_data["json_path"])
            assert json_path.exists(), f"JSON 文件不存在：{json_path}"

        # ========== Step 8: 验证可视化文件存在性 ==========
        rule13_dir = self.TEST_OUTPUT_BASE / "rule13"
        assert rule13_dir.exists()
        vis_files = list(rule13_dir.glob("*.png"))
        assert len(vis_files) == 3

        # 验证每个可视化文件存在且可读取
        for filename, img_data in images.items():
            vis_path = Path(img_data["vis_path"])
            assert vis_path.exists(), f"可视化文件不存在：{vis_path}"

            # 验证文件可以读取
            result_img = cv2.imread(str(vis_path))
            assert result_img is not None, f"无法读取可视化文件：{vis_path}"

        # ========== Step 9: 打印调试信息 ==========
        print(f"\n=== 完整流程测试通过 ===")
        print(f"输出目录：{self.TEST_OUTPUT_BASE}")
        print(f"可视化文件：{list(rule13_dir.glob('*.png'))}")
        print(f"JSON 文件：{list(scores_dir.glob('*.json'))}")
        print(f"\n各图片评分结果:")
        for filename, img_data in images.items():
            print(f"  {filename}: 海陆比={img_data['land_sea_ratio']:.2f}%, 得分={img_data['score']}")
        print(f"总分：{summary['total_score']}")
