# -*- coding: utf-8 -*-
"""
rule12_16_17 单元测试

全组合测试 RIB 连续性与主沟渲染功能：
- center_mode: none / RIB2-RIB3 / RIB3-RIB4 / RIB2-RIB3-RIB4  (4种)
- edge RIB1-RIB2: Y / N  (2种)
- edge RIB4-RIB5: Y / N  (2种)
共 4 × 2 × 2 = 16 种组合
"""

import shutil

import pytest
from pathlib import Path

from rules.rule12_16_17 import process_rib_continuity


# ── 全组合参数 ──────────────────────────────────────────
MODES = ["none", "RIB2-RIB3", "RIB3-RIB4", "RIB2-RIB3-RIB4"]
EDGE_VALUES = [True, False]

# 每种 center_mode 预期的 continuity_map
EXPECTED_CENTER = {
    "none":            {"RIB2-RIB3": "independent", "RIB3-RIB4": "independent"},
    "RIB2-RIB3":      {"RIB2-RIB3": "continuous",  "RIB3-RIB4": "independent"},
    "RIB3-RIB4":      {"RIB2-RIB3": "independent", "RIB3-RIB4": "continuous"},
    "RIB2-RIB3-RIB4": {"RIB2-RIB3": "continuous",  "RIB3-RIB4": "continuous"},
}


def _combo_id(mode, e12, e45):
    """生成可读的组合标签，如 'RIB2-RIB3__e12=Y_e45=N'"""
    tag_mode = mode if mode != "none" else "none"
    return f"{tag_mode}__e12={'Y' if e12 else 'N'}_e45={'Y' if e45 else 'N'}"


def _make_combos():
    """生成所有 16 种参数组合"""
    combos = []
    for mode in MODES:
        for e12 in EDGE_VALUES:
            for e45 in EDGE_VALUES:
                combos.append(
                    pytest.param(mode, e12, e45, id=_combo_id(mode, e12, e45))
                )
    return combos


# 测试所需的数据集路径
_TASK_ID = "rule12_16_17"
_BASE_PATH = ".results"

_DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "datasets"
_SRC_TASK_DIR = _DATASETS_DIR / f"task_id_{_TASK_ID}"
_SRC_SPLIT_CENTER = _SRC_TASK_DIR / "split" / "center_horz"
_SRC_SPLIT_SIDE = _SRC_TASK_DIR / "split" / "side_horz"

_SKIP_REASON = (
    f"测试数据集不存在: 需要 {_SRC_SPLIT_CENTER} 和 {_SRC_SPLIT_SIDE}"
)


@pytest.mark.skipif(
    not (_SRC_SPLIT_CENTER.exists() and _SRC_SPLIT_SIDE.exists()),
    reason=_SKIP_REASON,
)
class TestRule12_16_17:
    """rule12_16_17 RIB连续性与主沟渲染 — 全组合测试"""

    TASK_ID = _TASK_ID
    BASE_PATH = _BASE_PATH

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """每次测试前将 datasets/task_id_rule12_16_17 全量拷贝到 .results/"""
        dst = Path(self.BASE_PATH) / f"task_id_{self.TASK_ID}"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(_SRC_TASK_DIR, dst)

    def _run(self, mode: str, e12: bool, e45: bool, suffix: str):
        """通用执行器，edge 用 1.0/0.0 强制确定性"""
        conf = {
            "base_path": self.BASE_PATH,
            "continuity_mode": mode,
            "groove_width_mm": 10.0,
            "pixel_per_mm": 1.2,
            "blend_width": 10,
            "edge_continuity": {
                "RIB1-RIB2": 1.0 if e12 else 0.0,
                "RIB4-RIB5": 1.0 if e45 else 0.0,
            },
            "output_dir": f"rule12_16_17/{suffix}",
        }
        flag, result = process_rib_continuity(self.TASK_ID, conf)
        return flag, result, conf

    # ========== 16 种全组合 ==========

    @pytest.mark.parametrize("mode, e12, e45", _make_combos())
    def test_all_combos(self, mode, e12, e45):
        """
        参数化测试：验证每种组合的连续性标注与调试输出完整性

        对每种组合：
        1. flag=True
        2. center continuity_map 与预期一致
        3. edge continuity_map 与强制的 e12/e45 一致
        4. debug 目录结构完整（debug_annotated.png, debug_info.json, input/）
        5. 主沟数量=4, RIB宽度数量=5
        """
        combo_tag = _combo_id(mode, e12, e45)
        flag, result, conf = self._run(mode, e12, e45, combo_tag)

        assert flag is True, f"[{combo_tag}] flag={flag}, result={result}"
        assert result["task_id"] == self.TASK_ID

        dir_key = f"rule12_16_17/{combo_tag}"
        stats = result["directories"][dir_key]
        assert stats["success_count"] > 0, f"[{combo_tag}] 无成功图像"

        # 验证输出文件与调试目录
        task_dir = Path(self.BASE_PATH) / f"task_id_{self.TASK_ID}"
        output_dir = task_dir / "rule12_16_17" / combo_tag
        assert output_dir.exists(), f"输出目录不存在: {output_dir}"

        result_files = list(output_dir.glob("tread_*.png"))
        debug_dirs = [d for d in output_dir.glob("debug_*") if d.is_dir()]
        assert len(result_files) > 0, f"[{combo_tag}] 无结果图"
        assert len(debug_dirs) > 0, f"[{combo_tag}] 无调试目录"

        for dd in debug_dirs:
            assert (dd / "debug_annotated.png").exists(), f"缺失调试图: {dd}"
            assert (dd / "debug_info.json").exists(), f"缺失调试JSON: {dd}"
            assert (dd / "input").exists(), f"缺失input目录: {dd}"

        # 验证每张图像的元数据
        expected_center = EXPECTED_CENTER[mode]
        expected_edge12 = "continuous" if e12 else "independent"
        expected_edge45 = "continuous" if e45 else "independent"

        for img_name, img_info in stats["images"].items():
            if img_info["status"] != "success":
                continue
            cmap = img_info["continuity_map"]

            # center 连续性
            assert cmap["RIB2-RIB3"] == expected_center["RIB2-RIB3"], (
                f"[{combo_tag}] RIB2-RIB3: 期望{expected_center['RIB2-RIB3']}, 实际{cmap['RIB2-RIB3']}"
            )
            assert cmap["RIB3-RIB4"] == expected_center["RIB3-RIB4"], (
                f"[{combo_tag}] RIB3-RIB4: 期望{expected_center['RIB3-RIB4']}, 实际{cmap['RIB3-RIB4']}"
            )

            # edge 连续性
            assert cmap["RIB1-RIB2"] == expected_edge12, (
                f"[{combo_tag}] RIB1-RIB2: 期望{expected_edge12}, 实际{cmap['RIB1-RIB2']}"
            )
            assert cmap["RIB4-RIB5"] == expected_edge45, (
                f"[{combo_tag}] RIB4-RIB5: 期望{expected_edge45}, 实际{cmap['RIB4-RIB5']}"
            )

            # 结构完整性
            assert len(img_info["main_groove_positions"]) == 4, "5RIB应有4条主沟"
            assert len(img_info["actual_rib_widths"]) == 5, "应有5条RIB宽度"
            assert img_info["groove_width_px"] >= 1
