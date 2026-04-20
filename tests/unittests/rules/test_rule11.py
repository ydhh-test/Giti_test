# -*- coding: utf-8 -*-
"""
rule11 单元测试 - 纵向细沟 & 纵向钢片检测中间层（需求11）
"""

import json
import shutil
from pathlib import Path

import cv2
import numpy as np
import pytest

from rules.rule11 import (
    process_longitudinal_grooves,
    _process_single_image,
    _get_image_files,
    _aggregate_summary,
    _aggregate_dir_summary,
    _write_results_json,
)


# 测试数据集
_DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "datasets"
_SRC_TASK_DIR = _DATASETS_DIR / "task_longitudinal_groove_vis"

_SKIP_REASON = f"测试数据集不存在: 需要 {_SRC_TASK_DIR}"


class TestRule11Utilities:
    """rule11 工具函数单元测试"""

    # ------------------------------------------------------------------
    # _get_image_files
    # ------------------------------------------------------------------

    def test_get_image_files_sorted(self, tmp_path):
        """返回列表按文件名升序排列"""
        for name in ("c.png", "a.png", "b.png"):
            cv2.imwrite(str(tmp_path / name), np.zeros((4, 4, 3), dtype=np.uint8))
        files = _get_image_files(tmp_path)
        assert [f.name for f in files] == ["a.png", "b.png", "c.png"]

    def test_get_image_files_filters_non_image(self, tmp_path):
        """非图片文件不出现在结果中"""
        cv2.imwrite(str(tmp_path / "img.png"), np.zeros((4, 4, 3), dtype=np.uint8))
        (tmp_path / "notes.txt").write_text("ignore me")
        files = _get_image_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "img.png"

    def test_get_image_files_empty_dir(self, tmp_path):
        """空目录返回空列表"""
        assert _get_image_files(tmp_path) == []

    # ------------------------------------------------------------------
    # _aggregate_summary / _aggregate_dir_summary
    # ------------------------------------------------------------------

    def test_aggregate_summary_counts(self):
        results = [
            {"status": "ok",     "total_score": 4.0},
            {"status": "ok",     "total_score": 4.0},
            {"status": "failed", "err_msg": "读取失败"},
        ]
        s = _aggregate_summary(results)
        assert s["total_images"] == 3
        assert s["total_success"] == 2
        assert s["total_failed"] == 1
        assert s["total_score"] == 8.0

    def test_aggregate_dir_summary_totals(self):
        dir_stats = {
            "center_inf": {"total_count": 5, "processed_count": 5, "success_count": 4, "failed_count": 1, "skipped_count": 0, "total_score": 16.0, "images": {}},
            "side_inf":   {"total_count": 3, "processed_count": 3, "success_count": 3, "failed_count": 0, "skipped_count": 0, "total_score": 12.0, "images": {}},
        }
        s = _aggregate_dir_summary(dir_stats)
        assert s["total_images"] == 8
        assert s["total_success"] == 7
        assert s["total_failed"] == 1
        assert s["total_score"] == 28.0

    # ------------------------------------------------------------------
    # _write_results_json
    # ------------------------------------------------------------------

    def test_write_results_json_creates_file(self, tmp_path):
        results = [
            {"file": "a.png", "status": "ok", "total_score": 4.0, "debug_image": "a_debug.png"},
        ]
        _write_results_json(tmp_path, results)
        out = tmp_path / "results.json"
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["file"] == "a.png"


class TestRule11ProcessSingleImage:
    """_process_single_image 单元测试"""

    @staticmethod
    def _make_bgr_image(h=128, w=128, color=(200, 200, 200)):
        return np.full((h, w, 3), color, dtype=np.uint8)

    def test_process_single_image_ok(self, tmp_path):
        """合法图片返回 status='ok'，写出 debug 图"""
        img = self._make_bgr_image()
        img_path = tmp_path / "test.png"
        cv2.imwrite(str(img_path), img)

        out_dir = tmp_path / "output"
        out_dir.mkdir()

        ok, result = _process_single_image(img_path, "center", out_dir, {})
        assert ok is True
        assert result["status"] == "ok"
        assert "groove_count" in result
        assert "is_valid" in result
        assert "total_score" in result
        assert (out_dir / f"{img_path.stem}_debug.png").exists()

    def test_process_single_image_unreadable(self, tmp_path):
        """不可读文件返回 status='failed'"""
        bad_path = tmp_path / "bad.png"
        bad_path.write_text("not an image")

        out_dir = tmp_path / "output"
        out_dir.mkdir()

        ok, result = _process_single_image(bad_path, "center", out_dir, {})
        assert ok is False
        assert result["status"] == "failed"

    def test_process_single_image_side_type(self, tmp_path):
        """image_type='side' 正常执行"""
        img = self._make_bgr_image()
        img_path = tmp_path / "side_test.png"
        cv2.imwrite(str(img_path), img)

        out_dir = tmp_path / "output"
        out_dir.mkdir()

        ok, result = _process_single_image(img_path, "side", out_dir, {})
        assert ok is True
        assert result["rib_type"] == "RIB1/5"


@pytest.mark.skipif(
    not _SRC_TASK_DIR.exists(),
    reason=_SKIP_REASON,
)
class TestRule11Integration:
    """rule11 主入口集成测试（使用合成图像数据集）"""

    TASK_ID = "longitudinal_groove_vis"

    @pytest.fixture(autouse=True)
    def setup_task_dir(self, tmp_path):
        """将数据集拷贝到临时 .results 目录"""
        self.output_base = tmp_path
        task_dir = tmp_path / f"task_id_{self.TASK_ID}"
        shutil.copytree(_SRC_TASK_DIR, task_dir)
        yield

    def test_process_returns_true(self):
        """主函数返回 (True, dict)"""
        conf = {"output_base_dir": str(self.output_base)}
        flag, result = process_longitudinal_grooves(self.TASK_ID, conf)
        assert flag is True
        assert "task_id" in result
        assert "directories" in result
        assert "summary" in result

    def test_output_dirs_created(self):
        """检测输出目录被创建"""
        conf = {"output_base_dir": str(self.output_base)}
        process_longitudinal_grooves(self.TASK_ID, conf)

        task_dir = self.output_base / f"task_id_{self.TASK_ID}"
        center_out = task_dir / "detect_longitudinal_grooves" / "center"
        side_out   = task_dir / "detect_longitudinal_grooves" / "side"
        assert center_out.exists()
        assert side_out.exists()

    def test_results_json_written(self):
        """results.json 被写入每个输出子目录"""
        conf = {"output_base_dir": str(self.output_base)}
        process_longitudinal_grooves(self.TASK_ID, conf)

        task_dir = self.output_base / f"task_id_{self.TASK_ID}"
        for sub in ("center", "side"):
            rpath = task_dir / "detect_longitudinal_grooves" / sub / "results.json"
            assert rpath.exists()
            data = json.loads(rpath.read_text(encoding="utf-8"))
            assert len(data) > 0

    def test_debug_images_saved(self):
        """每张输入图对应一个 _debug.png"""
        conf = {"output_base_dir": str(self.output_base)}
        process_longitudinal_grooves(self.TASK_ID, conf)

        task_dir = self.output_base / f"task_id_{self.TASK_ID}"
        center_out = task_dir / "detect_longitudinal_grooves" / "center"
        debug_files = list(center_out.glob("*_debug.png"))
        assert len(debug_files) > 0

    def test_summary_score_nonnegative(self):
        """汇总分数 >= 0"""
        conf = {"output_base_dir": str(self.output_base)}
        flag, result = process_longitudinal_grooves(self.TASK_ID, conf)
        assert result["summary"]["total_score"] >= 0

    def test_center_groove_count_in_results(self):
        """center 图片结果中包含 groove_count 字段"""
        conf = {"output_base_dir": str(self.output_base)}
        flag, result = process_longitudinal_grooves(self.TASK_ID, conf)

        center_stats = result["directories"].get("center_inf", {})
        for img_name, img_result in center_stats.get("images", {}).items():
            if img_result["status"] == "ok":
                assert "groove_count" in img_result
                assert isinstance(img_result["groove_count"], int)

    def test_missing_input_dir_skipped(self):
        """输入目录不存在时跳过且不报错"""
        conf = {
            "output_base_dir": str(self.output_base),
            "input_dirs": {"nonexistent_dir": "center"},
        }
        flag, result = process_longitudinal_grooves(self.TASK_ID, conf)
        assert flag is True
        stats = result["directories"]["nonexistent_dir"]
        assert stats["total_count"] == 0
