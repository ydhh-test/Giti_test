# -*- coding: utf-8 -*-
"""
rule9_10 单元测试 - 横向钢片检测中间层（需求9 & 需求10）
"""

import json
import shutil
from pathlib import Path

import cv2
import numpy as np
import pytest

from rules.rule9_10 import (
    process_horizontal_sipes,
    _process_single_image,
    _get_image_files,
    _aggregate_summary,
    _aggregate_dir_summary,
    _write_results_json,
)


class TestRule9_10:
    """rule9_10 中间层单元测试"""

    TEST_TASK_ID = "test_rule9_10"
    DATASET_BASE = Path("tests/datasets/task_id_test_rule9_10")
    TEST_OUTPUT_BASE = Path(".results") / f"task_id_{TEST_TASK_ID}"

    # 与 rule9_10._DETECTOR_DIR 保持一致
    DETECTOR_DIR = "detect_horizontal_sipes"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """每个测试前：清理旧目录、准备生产输入目录。测试后保留输出便于手工验证。"""
        if self.TEST_OUTPUT_BASE.exists():
            shutil.rmtree(self.TEST_OUTPUT_BASE)
        self.TEST_OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
        yield

    # ------------------------------------------------------------------
    # 工具函数 — _get_image_files
    # ------------------------------------------------------------------

    def test_get_image_files_sorted(self, tmp_path):
        """返回列表按文件名升序排列"""
        for name in ("c.png", "a.png", "b.png"):
            cv2.imwrite(str(tmp_path / name), np.zeros((4, 4, 3), dtype=np.uint8))
        files = _get_image_files(tmp_path)
        assert [f.name for f in files] == ["a.png", "b.png", "c.png"]

    def test_get_image_files_filters_non_image(self, tmp_path):
        """非图片文件（.txt）不出现在结果中"""
        cv2.imwrite(str(tmp_path / "img.png"), np.zeros((4, 4, 3), dtype=np.uint8))
        (tmp_path / "notes.txt").write_text("ignore me")
        files = _get_image_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "img.png"

    def test_get_image_files_empty_dir(self, tmp_path):
        """空目录返回空列表"""
        assert _get_image_files(tmp_path) == []

    # ------------------------------------------------------------------
    # 工具函数 — _aggregate_summary / _aggregate_dir_summary
    # ------------------------------------------------------------------

    def test_aggregate_summary_counts(self):
        results = [
            {"status": "ok",     "total_score": 8.0},
            {"status": "ok",     "total_score": 4.0},
            {"status": "failed", "err_msg": "读取失败"},
        ]
        s = _aggregate_summary(results)
        assert s["total_images"] == 3
        assert s["total_processed"] == 3
        assert s["total_success"] == 2
        assert s["total_failed"] == 1
        assert s["total_skipped"] == 0
        assert s["total_score"] == 12.0

    def test_aggregate_dir_summary_totals(self):
        dir_stats = {
            "center_inf": {"total_count": 5, "processed_count": 5, "success_count": 4, "failed_count": 1, "skipped_count": 0, "total_score": 32.0, "images": {}},
            "side_inf":   {"total_count": 3, "processed_count": 3, "success_count": 3, "failed_count": 0, "skipped_count": 0, "total_score": 24.0, "images": {}},
        }
        s = _aggregate_dir_summary(dir_stats)
        assert s["total_images"] == 8
        assert s["total_processed"] == 8
        assert s["total_success"] == 7
        assert s["total_failed"] == 1
        assert s["total_skipped"] == 0
        assert s["total_score"] == 56.0

    # ------------------------------------------------------------------
    # 工具函数 — _write_results_json
    # ------------------------------------------------------------------

    def test_write_results_json_creates_file(self, tmp_path):
        results = [
            {"file": "a.png", "status": "ok", "total_score": 8.0, "debug_image": "a_debug.png"},
        ]
        _write_results_json(tmp_path, results)
        out = tmp_path / "results.json"
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["file"] == "a.png"

    # ------------------------------------------------------------------
    # _process_single_image
    # ------------------------------------------------------------------

    def _make_bgr_image(self, h=128, w=128, color=(200, 200, 200)):
        return np.full((h, w, 3), color, dtype=np.uint8)

    def test_process_single_image_ok(self, tmp_path):
        """合法图片返回 status='ok'，写出 debug 图"""
        fpath = tmp_path / "test.png"
        cv2.imwrite(str(fpath), self._make_bgr_image())
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        ok, result = _process_single_image(fpath, "center", out_dir, {})

        assert ok is True
        assert result["status"] == "ok"
        assert result["file"] == "test.png"
        assert (out_dir / result["debug_image"]).exists()
        assert "sipe_count" in result
        assert "groove_count" in result
        assert 0.0 <= result["total_score"] <= 8.0

    def test_process_single_image_side_ok(self, tmp_path):
        """side image_type 也能正常处理"""
        fpath = tmp_path / "s.png"
        cv2.imwrite(str(fpath), self._make_bgr_image())
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        ok, result = _process_single_image(fpath, "side", out_dir, {})

        assert ok is True
        assert result["rib_type"] == "RIB1/5"
        assert 0.0 <= result["total_score"] <= 8.0

    def test_process_single_image_unreadable(self, tmp_path):
        """无效文件返回 status='failed'"""
        fpath = tmp_path / "bad.png"
        fpath.write_bytes(b"not an image")
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        ok, result = _process_single_image(fpath, "center", out_dir, {})

        assert ok is False
        assert result["status"] == "failed"
        assert "err_msg" in result

    def test_process_single_image_debug_name(self, tmp_path):
        """debug 图文件名为 {stem}_debug.png"""
        fpath = tmp_path / "image_3.png"
        cv2.imwrite(str(fpath), self._make_bgr_image())
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        _, result = _process_single_image(fpath, "center", out_dir, {})
        assert result["debug_image"] == "image_3_debug.png"

    def test_process_single_image_custom_pixel_per_mm(self, tmp_path):
        """conf 中的 pixel_per_mm 被正确透传"""
        fpath = tmp_path / "x.png"
        cv2.imwrite(str(fpath), self._make_bgr_image())
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        ok, _ = _process_single_image(fpath, "center", out_dir, {"pixel_per_mm": 5.0})
        assert ok is True

    # ------------------------------------------------------------------
    # process_horizontal_sipes — 边界条件
    # ------------------------------------------------------------------

    def _conf(self, **extra):
        base = {"output_base_dir": str(Path(".results"))}
        base.update(extra)
        return base

    def test_nonexistent_input_dir_returns_empty_stats(self):
        """输入目录不存在：返回 True + 空统计，不报错"""
        flag, details = process_horizontal_sipes(
            self.TEST_TASK_ID,
            self._conf(input_dirs={"nonexistent_dir": "center"})
        )
        assert flag is True
        assert details["summary"]["total_images"] == 0
        assert details["summary"]["total_processed"] == 0
        assert details["summary"]["total_success"] == 0

    def test_empty_input_dir_returns_empty_stats(self):
        """输入目录存在但为空：返回 True + 空统计"""
        empty_dir = self.TEST_OUTPUT_BASE / "empty_inf"
        empty_dir.mkdir(parents=True, exist_ok=True)

        flag, details = process_horizontal_sipes(
            self.TEST_TASK_ID,
            self._conf(input_dirs={"empty_inf": "center"})
        )
        assert flag is True
        assert details["summary"]["total_images"] == 0

    def test_output_structure(self):
        """返回值包含 task_id / directories / summary 三个顶层键"""
        flag, details = process_horizontal_sipes(
            self.TEST_TASK_ID,
            self._conf(input_dirs={"nonexistent_dir": "center"})
        )
        assert flag is True
        assert "task_id" in details
        assert "directories" in details
        assert "summary" in details

    def test_custom_input_dirs_override(self):
        """conf['input_dirs'] 可覆盖默认目录映射"""
        custom_dir = self.TEST_OUTPUT_BASE / "my_center"
        custom_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(custom_dir / "img.png"), self._make_bgr_image())

        flag, details = process_horizontal_sipes(
            self.TEST_TASK_ID,
            self._conf(input_dirs={"my_center": "center"})
        )
        assert flag is True
        assert "my_center" in details["directories"]
        assert details["directories"]["my_center"]["total_count"] == 1

    # ------------------------------------------------------------------
    # process_horizontal_sipes — 完整流程（使用真实测试数据集）
    # ------------------------------------------------------------------

    def _copy_dataset(self, src_subdir: str, dst_subdir: str) -> int:
        """
        将 tests/datasets/{DATASET}/{src_subdir}/ 拷贝到
        .results/task_id_{TEST_TASK_ID}/{dst_subdir}/（模拟生产输入目录）。
        返回拷贝的图片数量。
        """
        src = self.DATASET_BASE / src_subdir
        dst = self.TEST_OUTPUT_BASE / dst_subdir
        if not src.exists():
            return 0
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(str(src), str(dst))
        return sum(1 for f in dst.iterdir() if f.suffix.lower() in (".png", ".jpg", ".jpeg"))

    def test_full_center_and_side(self):
        """
        完整流程正例：center_inf + side_inf 真实图片，
        验证输出文件、results.json 字段完整性。
        """
        n_center = self._copy_dataset("center_inf", "center_inf")
        n_side = self._copy_dataset("side_inf", "side_inf")

        if n_center == 0 and n_side == 0:
            pytest.skip("测试数据集不存在")

        flag, details = process_horizontal_sipes(self.TEST_TASK_ID, self._conf())

        assert flag is True
        assert details["task_id"] == self.TEST_TASK_ID

        # --- center 检验 ---
        if n_center > 0:
            center_stats = details["directories"]["center_inf"]
            assert center_stats["total_count"] == n_center
            assert center_stats["processed_count"] == n_center
            assert center_stats["success_count"] + center_stats["failed_count"] == n_center

            center_out = self.TEST_OUTPUT_BASE / self.DETECTOR_DIR / "center"
            assert center_out.exists()

            # results.json 存在且包含正确数量的条目
            rj = center_out / "results.json"
            assert rj.exists()
            data = json.loads(rj.read_text(encoding="utf-8"))
            assert len(data) == n_center

            # 每条记录包含必要字段
            required = {"file", "status", "sipe_count", "groove_count",
                        "total_score", "debug_image"}
            for entry in data:
                assert required.issubset(entry.keys()), f"缺少字段: {required - entry.keys()}"

            # 调试图文件存在
            for entry in data:
                if entry["status"] == "ok":
                    assert (center_out / entry["debug_image"]).exists()

        # --- side 检验 ---
        if n_side > 0:
            side_stats = details["directories"]["side_inf"]
            assert side_stats["total_count"] == n_side

            side_out = self.TEST_OUTPUT_BASE / self.DETECTOR_DIR / "side"
            assert side_out.exists()
            assert (side_out / "results.json").exists()

        # --- 整体 summary ---
        s = details["summary"]
        assert s["total_images"] == n_center + n_side
        assert s["total_success"] + s["total_failed"] == s["total_images"]

    def test_full_center_only(self):
        """只提供 center_inf，side_inf 缺失时不报错"""
        n_center = self._copy_dataset("center_inf", "center_inf")
        if n_center == 0:
            pytest.skip("center_inf 测试数据集不存在")

        flag, details = process_horizontal_sipes(
            self.TEST_TASK_ID,
            self._conf(input_dirs={"center_inf": "center"})
        )
        assert flag is True
        assert details["directories"]["center_inf"]["total_count"] == n_center

        # 验证 center 调试图和 results.json 存在
        center_out = self.TEST_OUTPUT_BASE / self.DETECTOR_DIR / "center"
        assert center_out.exists()
        data = json.loads((center_out / "results.json").read_text(encoding="utf-8"))
        assert len(data) == n_center
        for entry in data:
            if entry["status"] == "ok":
                assert entry["rib_type"] == "RIB2/3/4"
                assert 0.0 <= entry["total_score"] <= 8.0
                assert (center_out / entry["debug_image"]).exists()

    def test_full_side_only(self):
        """只提供 side_inf，center_inf 缺失时不报错"""
        n_side = self._copy_dataset("side_inf", "side_inf")
        if n_side == 0:
            pytest.skip("side_inf 测试数据集不存在")

        flag, details = process_horizontal_sipes(
            self.TEST_TASK_ID,
            self._conf(input_dirs={"side_inf": "side"})
        )
        assert flag is True
        assert details["directories"]["side_inf"]["total_count"] == n_side

        # 验证 side 调试图和 results.json 存在
        side_out = self.TEST_OUTPUT_BASE / self.DETECTOR_DIR / "side"
        assert side_out.exists()
        data = json.loads((side_out / "results.json").read_text(encoding="utf-8"))
        assert len(data) == n_side
        for entry in data:
            if entry["status"] == "ok":
                assert entry["rib_type"] == "RIB1/5"
                assert 0.0 <= entry["total_score"] <= 8.0
                assert (side_out / entry["debug_image"]).exists()

    def test_score_range_on_real_images(self):
        """真实图片（center + side）上每张的 total_score 在 [0, 8] 范围内"""
        n_center = self._copy_dataset("center_inf", "center_inf")
        n_side = self._copy_dataset("side_inf", "side_inf")
        if n_center == 0 and n_side == 0:
            pytest.skip("测试数据集不存在")

        _, details = process_horizontal_sipes(self.TEST_TASK_ID, self._conf())

        # 检查 center
        if n_center > 0:
            center_out = self.TEST_OUTPUT_BASE / self.DETECTOR_DIR / "center"
            data = json.loads((center_out / "results.json").read_text(encoding="utf-8"))
            for entry in data:
                if entry["status"] == "ok":
                    assert 0.0 <= entry["total_score"] <= 8.0, (
                        f"{entry['file']} total_score={entry['total_score']} 超出范围"
                    )

        # 检查 side
        if n_side > 0:
            side_out = self.TEST_OUTPUT_BASE / self.DETECTOR_DIR / "side"
            data = json.loads((side_out / "results.json").read_text(encoding="utf-8"))
            for entry in data:
                if entry["status"] == "ok":
                    assert 0.0 <= entry["total_score"] <= 8.0, (
                        f"{entry['file']} total_score={entry['total_score']} 超出范围"
                    )
