# -*- coding: utf-8 -*-
"""
rule16_17 单元测试

测试 RIB 连续性与主沟渲染功能：
- TC-01: 基线拼接（无连续性处理，仅主沟）
- TC-02: 双RIB连续 RIB2-RIB3 模式
- TC-03: 双RIB连续 RIB3-RIB4 模式
- TC-04: 三RIB连续 RIB2-RIB3-RIB4 模式
- TC-05: 无连续性模式 none
"""

import pytest
from pathlib import Path

from rules.rule16_17 import process_rib_continuity


class TestRule16_17:
    """rule16_17 RIB连续性与主沟渲染单元测试"""

    TASK_ID = "1778457600"
    BASE_PATH = ".results"

    def _run_with_mode(self, mode: str, suffix: str = ""):
        """通用测试执行器"""
        conf = {
            "base_path": self.BASE_PATH,
            "continuity_mode": mode,
            "groove_width_mm": 10.0,
            "pixel_per_mm": 1.2,
            "blend_width": 10,
            "edge_continuity": {
                "RIB1-RIB2": 0.5,
                "RIB4-RIB5": 0.5,
            },
            "output_dir": f"rule16_17{suffix}",
        }

        flag, result = process_rib_continuity(self.TASK_ID, conf)
        return flag, result, conf

    # ========== TC-01: 基线拼接（无连续性） ==========

    def test_TC01_baseline_no_continuity(self):
        """
        TC-01: 无连续性模式，仅测试基本拼接+主沟渲染

        输入: split/center_horz (part2/3/4) + split/side_horz (part1/5)
        配置: continuity_mode="none"
        预期: flag=True, 生成带主沟的完整胎面图
        """
        flag, result, conf = self._run_with_mode("none", "_TC01")

        assert flag is True, f"期望 flag=True, 实际={flag}, result={result}"
        assert result["task_id"] == self.TASK_ID

        stats = result["directories"]["rule16_17_TC01"]
        assert stats["success_count"] > 0, f"期望至少1张成功, 实际={stats['success_count']}"

        # 验证文件存在
        task_dir = Path(self.BASE_PATH) / f"task_id_{self.TASK_ID}"
        output_dir = task_dir / f"rule16_17_TC01"
        debug_dir = output_dir / "debug"
        assert output_dir.exists(), f"输出目录应存在: {output_dir}"
        assert debug_dir.exists(), f"调试目录应存在: {debug_dir}"

        result_files = list(output_dir.glob("*.png"))
        debug_files = list(debug_dir.glob("*_debug.png"))
        assert len(result_files) > 0, "应至少生成1张结果图"
        assert len(debug_files) > 0, "应至少生成1张调试图"

        # 验证图像元数据
        for img_info in stats["images"].values():
            if img_info["status"] == "success":
                assert "continuity_map" in img_info
                assert "main_groove_positions" in img_info
                assert "actual_rib_widths" in img_info
                assert len(img_info["main_groove_positions"]) == 4, "5RIB应有4条主沟"
                assert len(img_info["actual_rib_widths"]) == 5, "应有5条RIB宽度"
                # none模式下中间RIB均为independent
                assert img_info["continuity_map"]["RIB2-RIB3"] == "independent"
                assert img_info["continuity_map"]["RIB3-RIB4"] == "independent"

    # ========== TC-02: 双RIB连续 RIB2-RIB3 ==========

    def test_TC02_pair_rib2_rib3(self):
        """
        TC-02: RIB2-RIB3 双RIB连续模式

        配置: continuity_mode="RIB2-RIB3"
        预期: RIB2-RIB3连续, RIB3-RIB4独立
        """
        flag, result, _ = self._run_with_mode("RIB2-RIB3", "_TC02")

        assert flag is True, f"result={result}"

        stats = result["directories"]["rule16_17_TC02"]
        for img_info in stats["images"].values():
            if img_info["status"] == "success":
                assert img_info["continuity_map"]["RIB2-RIB3"] == "continuous"
                assert img_info["continuity_map"]["RIB3-RIB4"] == "independent"

    # ========== TC-03: 双RIB连续 RIB3-RIB4 ==========

    def test_TC03_pair_rib3_rib4(self):
        """
        TC-03: RIB3-RIB4 双RIB连续模式

        配置: continuity_mode="RIB3-RIB4"
        预期: RIB2-RIB3独立, RIB3-RIB4连续
        """
        flag, result, _ = self._run_with_mode("RIB3-RIB4", "_TC03")

        assert flag is True, f"result={result}"

        stats = result["directories"]["rule16_17_TC03"]
        for img_info in stats["images"].values():
            if img_info["status"] == "success":
                assert img_info["continuity_map"]["RIB2-RIB3"] == "independent"
                assert img_info["continuity_map"]["RIB3-RIB4"] == "continuous"

    # ========== TC-04: 三RIB连续 RIB2-RIB3-RIB4 ==========

    def test_TC04_triple_rib2_rib3_rib4(self):
        """
        TC-04: RIB2-RIB3-RIB4 三RIB全连续模式

        配置: continuity_mode="RIB2-RIB3-RIB4"
        预期: RIB2-RIB3 和 RIB3-RIB4 均连续
        """
        flag, result, _ = self._run_with_mode("RIB2-RIB3-RIB4", "_TC04")

        assert flag is True, f"result={result}"

        stats = result["directories"]["rule16_17_TC04"]
        for img_info in stats["images"].values():
            if img_info["status"] == "success":
                assert img_info["continuity_map"]["RIB2-RIB3"] == "continuous"
                assert img_info["continuity_map"]["RIB3-RIB4"] == "continuous"

    # ========== TC-05: 验证输出宽度匹配原图 ==========

    def test_TC05_output_width_matches_original(self):
        """
        TC-05: 验证输出图宽度与原始图像一致

        当 images/ 目录存在原始图像时，主沟宽度应自动计算，
        使得输出总宽度 = 原始图像宽度。
        """
        flag, result, _ = self._run_with_mode("none", "_TC05")

        assert flag is True

        stats = result["directories"]["rule16_17_TC05"]
        for img_info in stats["images"].values():
            if img_info["status"] == "success":
                # 若有 target_width，输出宽度应等于 target_width
                target_w = img_info.get("target_width")
                if target_w is not None:
                    actual_w = img_info["image_size"][1]
                    assert actual_w == target_w, (
                        f"输出宽度={actual_w}px 应等于原图宽度={target_w}px"
                    )
                # 所有主沟应等宽（groove_width_px 是统一值）
                assert img_info["groove_width_px"] >= 1, (
                    f"主沟宽度应>=1px, 实际={img_info['groove_width_px']}"
                )
