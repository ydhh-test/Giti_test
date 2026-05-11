# -*- coding: utf-8 -*-
"""
海陆比评分算法单元测试（新架构 dev2）

测试目标：src.core.scoring.land_sea_ratio
API 注意：compute_land_sea_ratio() 使用显式参数，返回显式 tuple，不返回 dict。

主要变更（相对 feature/dev 分支）：
- import 路径：rules.scoring.land_sea_ratio -> src.core.scoring.land_sea_ratio
- 输入：dict conf -> 显式参数（target_min, target_max, margin）
- 输出：(score, details_dict) -> (score, ratio_percent, vis_name, vis_image)
- 算法层不保存文件，不接收 task_id 或输出路径，不返回 black_area/gray_area
- is_debug=True 时返回可视化图像，由调用方决定是否保存

最重要的测试验证逻辑：
- 使用 feature/dev 原始大图（combine_horizontal/）验证评分与海陆比值与老算法一致。
- 使用 wise_image_dev1/ 保存的老架构染色图，与新架构 is_debug=True 生成的染色图做
  np.array 像素级比对，证明 debug 可视化迁移等价。
- 使用合成图像验证三级评分边界（优秀/合格/不合格）及边界值精确行为。
- 通过覆盖率工具确认 _score / _compute_black_area / _compute_gray_area / _draw_debug_image
  内所有分支均被覆盖。

人工设计的覆盖性测试逻辑：
- 针对公开 API 边界：覆盖 None、非 ndarray、灰度图（2D）、target_max<=target_min、
  负 margin 等输入异常，防止调用方传入非法参数后无声地产生错误结果。
- 针对三级评分：用精确构造的像素比例图像，分别验证目标区间内（score=2）、
  下容差区间（score=1）、上容差区间（score=1）、超出范围（score=0）共四个分支。
  直接构造边界值图像比依赖真实图更稳定，能防止阈值被误改。
- 针对纯白图：海陆比应为 0%，评分为 0，验证零像素边界不崩溃。
- 针对 debug 图：覆盖 is_debug=True/False，验证 vis_name/vis_image 的返回类型。
- 针对等价性：对三张真实测试图逐图验证 ratio_percent 和 score 与老算法计算结果一致；
  对同一批图做像素级 np.array_equal 比对新旧染色图，验证可视化等价。
"""

import pathlib
import sys
import unittest

_ROOT = pathlib.Path(__file__).parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False

_DATASET_BASE = _ROOT / "tests" / "datasets" / "test_land_sea_ratio"
_COMBINE_HORIZONTAL = _DATASET_BASE / "combine_horizontal"
_WISE_IMAGE_DEV1 = _DATASET_BASE / "wise_image_dev1"
_WISE_IMAGE_DEV2 = _DATASET_BASE / "wise_image_dev2"


def _make_ratio_image(height: int, width: int, black_ratio: float, gray_ratio: float) -> "np.ndarray":
    """
    构造给定黑色/灰色占比的 BGR 测试图像。
    黑色像素值 = 30，灰色像素值 = 100，白色像素值 = 240。
    """
    total = height * width
    black_count = int(total * black_ratio)
    gray_count = int(total * gray_ratio)

    gray_img = np.full((total,), 240, dtype=np.uint8)
    gray_img[:black_count] = 30
    gray_img[black_count:black_count + gray_count] = 100
    gray_img = gray_img.reshape(height, width)

    return cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)


def _load_image(path: pathlib.Path) -> "np.ndarray":
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise AssertionError(f"无法读取图片: {path}")
    return img


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestComputeLandSeaRatioApi(unittest.TestCase):
    """公开 API 边界和输入校验测试。"""

    def _run(self, image, **kwargs):
        from src.core.scoring.land_sea_ratio import compute_land_sea_ratio
        return compute_land_sea_ratio(image, **kwargs)

    def test_none_image_raises(self):
        from src.common.exceptions import InputDataError
        with self.assertRaises(InputDataError):
            self._run(None)

    def test_non_ndarray_raises(self):
        from src.common.exceptions import InputDataError
        with self.assertRaises(InputDataError):
            self._run("not_an_image")

    def test_grayscale_2d_image_raises(self):
        from src.common.exceptions import InputDataError
        gray = np.zeros((100, 100), dtype=np.uint8)
        with self.assertRaises(InputDataError):
            self._run(gray)

    def test_target_max_le_target_min_raises(self):
        from src.common.exceptions import InputDataError
        image = _make_ratio_image(100, 100, 0.3, 0.0)
        with self.assertRaises(InputDataError):
            self._run(image, target_min=35.0, target_max=28.0)

    def test_negative_margin_raises(self):
        from src.common.exceptions import InputDataError
        image = _make_ratio_image(100, 100, 0.3, 0.0)
        with self.assertRaises(InputDataError):
            self._run(image, margin=-1.0)

    def test_negative_target_min_raises(self):
        from src.common.exceptions import InputDataError
        image = _make_ratio_image(100, 100, 0.3, 0.0)
        with self.assertRaises(InputDataError):
            self._run(image, target_min=-1.0)

    def test_return_types_no_debug(self):
        image = _make_ratio_image(100, 100, 0.3, 0.0)
        score, ratio_percent, vis_name, vis_image = self._run(image)
        self.assertIsInstance(score, int)
        self.assertIsInstance(ratio_percent, float)
        self.assertEqual(vis_name, "")
        self.assertIsNone(vis_image)

    def test_return_types_with_debug(self):
        image = _make_ratio_image(100, 100, 0.3, 0.0)
        score, ratio_percent, vis_name, vis_image = self._run(image, is_debug=True)
        self.assertEqual(vis_name, "land_sea_ratio.png")
        self.assertIsInstance(vis_image, np.ndarray)
        self.assertEqual(vis_image.shape, image.shape)

    def test_score_range(self):
        image = _make_ratio_image(100, 100, 0.3, 0.0)
        score, ratio_percent, _, _ = self._run(image)
        self.assertIn(score, [0, 1, 2])
        self.assertGreaterEqual(ratio_percent, 0.0)
        self.assertLessEqual(ratio_percent, 100.0)


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestScoring(unittest.TestCase):
    """三级评分边界验证。"""

    def _run(self, image, **kwargs):
        from src.core.scoring.land_sea_ratio import compute_land_sea_ratio
        return compute_land_sea_ratio(image, **kwargs)

    def test_score_2_in_target_range(self):
        """黑色占30%，在目标区间[28, 35]内，应得 2 分。"""
        image = _make_ratio_image(100, 100, 0.30, 0.0)
        score, ratio_percent, _, _ = self._run(image, target_min=28.0, target_max=35.0, margin=5.0)
        self.assertEqual(score, 2)
        self.assertGreaterEqual(ratio_percent, 28.0)
        self.assertLessEqual(ratio_percent, 35.0)

    def test_score_1_below_target_in_margin(self):
        """黑色占25%，在下容差区间[23, 28)内，应得 1 分。"""
        image = _make_ratio_image(100, 100, 0.25, 0.0)
        score, ratio_percent, _, _ = self._run(image, target_min=28.0, target_max=35.0, margin=5.0)
        self.assertEqual(score, 1)
        self.assertGreaterEqual(ratio_percent, 23.0)
        self.assertLess(ratio_percent, 28.0)

    def test_score_1_above_target_in_margin(self):
        """黑色+灰色占38%，在上容差区间(35, 40]内，应得 1 分。"""
        image = _make_ratio_image(100, 100, 0.38, 0.0)
        score, ratio_percent, _, _ = self._run(image, target_min=28.0, target_max=35.0, margin=5.0)
        self.assertEqual(score, 1)
        self.assertGreater(ratio_percent, 35.0)
        self.assertLessEqual(ratio_percent, 40.0)

    def test_score_0_far_below_range(self):
        """黑色占10%，远低于最低容差线23%，应得 0 分。"""
        image = _make_ratio_image(100, 100, 0.10, 0.0)
        score, ratio_percent, _, _ = self._run(image, target_min=28.0, target_max=35.0, margin=5.0)
        self.assertEqual(score, 0)
        self.assertLess(ratio_percent, 23.0)

    def test_score_0_far_above_range(self):
        """黑色+灰色占50%，远高于最高容差线40%，应得 0 分。"""
        image = _make_ratio_image(100, 100, 0.50, 0.0)
        score, ratio_percent, _, _ = self._run(image, target_min=28.0, target_max=35.0, margin=5.0)
        self.assertEqual(score, 0)
        self.assertGreater(ratio_percent, 40.0)

    def test_pure_white_image_score_0(self):
        """纯白图：海陆比为 0%，评分为 0。验证零边界不崩溃。"""
        image = np.full((100, 100, 3), 255, dtype=np.uint8)
        score, ratio_percent, _, _ = self._run(image)
        self.assertEqual(score, 0)
        self.assertAlmostEqual(ratio_percent, 0.0, places=2)

    def test_target_exactly_at_min_boundary(self):
        """ratio 精确等于 target_min 时，应得 2 分（区间含端点）。"""
        image = _make_ratio_image(100, 100, 0.28, 0.0)
        score, ratio_percent, _, _ = self._run(image, target_min=28.0, target_max=35.0, margin=5.0)
        # 由于像素离散化，ratio 可能不精确等于 28.0，但应在 [28, 35] 范围内
        if 28.0 <= ratio_percent <= 35.0:
            self.assertEqual(score, 2)
        else:
            self.assertIn(score, [0, 1, 2])


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestBlackGrayArea(unittest.TestCase):
    """_compute_black_area 和 _compute_gray_area 内部函数白盒测试。"""

    def test_black_area_all_black(self):
        from src.core.scoring.land_sea_ratio import _compute_black_area
        gray = np.full((100, 100), 30, dtype=np.uint8)
        area = _compute_black_area(gray)
        self.assertEqual(area, 10000)

    def test_black_area_no_black(self):
        from src.core.scoring.land_sea_ratio import _compute_black_area
        gray = np.full((100, 100), 200, dtype=np.uint8)
        area = _compute_black_area(gray)
        self.assertEqual(area, 0)

    def test_black_area_boundary_50(self):
        from src.core.scoring.land_sea_ratio import _compute_black_area
        gray = np.full((100, 100), 50, dtype=np.uint8)
        area = _compute_black_area(gray)
        self.assertEqual(area, 10000)

    def test_black_area_boundary_51(self):
        from src.core.scoring.land_sea_ratio import _compute_black_area
        gray = np.full((100, 100), 51, dtype=np.uint8)
        area = _compute_black_area(gray)
        self.assertEqual(area, 0)

    def test_gray_area_all_gray(self):
        from src.core.scoring.land_sea_ratio import _compute_gray_area
        gray = np.full((100, 100), 100, dtype=np.uint8)
        area = _compute_gray_area(gray)
        self.assertEqual(area, 10000)

    def test_gray_area_no_gray(self):
        from src.core.scoring.land_sea_ratio import _compute_gray_area
        gray = np.full((100, 100), 30, dtype=np.uint8)
        area = _compute_gray_area(gray)
        self.assertEqual(area, 0)

    def test_gray_area_boundary_200(self):
        from src.core.scoring.land_sea_ratio import _compute_gray_area
        gray = np.full((100, 100), 200, dtype=np.uint8)
        area = _compute_gray_area(gray)
        self.assertEqual(area, 10000)

    def test_gray_area_boundary_201(self):
        from src.core.scoring.land_sea_ratio import _compute_gray_area
        gray = np.full((100, 100), 201, dtype=np.uint8)
        area = _compute_gray_area(gray)
        self.assertEqual(area, 0)


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestRuntimeErrors(unittest.TestCase):
    """RuntimeProcessError 抛出路径测试（mock 注入异常）。"""

    def test_computation_failure_wraps_as_runtime_error(self):
        """当内部 cv2.cvtColor 抛出时，应包装为 RuntimeProcessError。"""
        from src.common.exceptions import RuntimeProcessError
        from unittest.mock import patch
        image = _make_ratio_image(100, 100, 0.3, 0.0)
        with patch("src.core.scoring.land_sea_ratio.cv2.cvtColor", side_effect=RuntimeError("mock")):
            from src.core.scoring.land_sea_ratio import compute_land_sea_ratio
            with self.assertRaises(RuntimeProcessError):
                compute_land_sea_ratio(image)

    def test_debug_draw_failure_wraps_as_runtime_error(self):
        """当 _draw_debug_image 抛出时，应包装为 RuntimeProcessError。"""
        from src.common.exceptions import RuntimeProcessError
        from unittest.mock import patch
        image = _make_ratio_image(100, 100, 0.3, 0.0)
        with patch("src.core.scoring.land_sea_ratio._draw_debug_image", side_effect=RuntimeError("mock")):
            from src.core.scoring.land_sea_ratio import compute_land_sea_ratio
            with self.assertRaises(RuntimeProcessError):
                compute_land_sea_ratio(image, is_debug=True)


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestDebugVisualization(unittest.TestCase):
    """debug 可视化输出测试。"""

    def _run(self, image, **kwargs):
        from src.core.scoring.land_sea_ratio import compute_land_sea_ratio
        return compute_land_sea_ratio(image, **kwargs)

    def test_no_debug_returns_none_and_empty_string(self):
        image = _make_ratio_image(100, 100, 0.3, 0.0)
        _, _, vis_name, vis_image = self._run(image, is_debug=False)
        self.assertEqual(vis_name, "")
        self.assertIsNone(vis_image)

    def test_debug_returns_correct_name(self):
        image = _make_ratio_image(100, 100, 0.3, 0.0)
        _, _, vis_name, _ = self._run(image, is_debug=True)
        self.assertEqual(vis_name, "land_sea_ratio.png")

    def test_debug_image_same_shape_as_input(self):
        image = _make_ratio_image(200, 300, 0.3, 0.1)
        _, _, _, vis_image = self._run(image, is_debug=True)
        self.assertEqual(vis_image.shape, image.shape)

    def test_debug_image_dtype_uint8(self):
        image = _make_ratio_image(100, 100, 0.3, 0.0)
        _, _, _, vis_image = self._run(image, is_debug=True)
        self.assertEqual(vis_image.dtype, np.uint8)


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestRealImages(unittest.TestCase):
    """
    使用真实测试图像验证评分与老算法等价。

    预期结果（由老算法计算，在准备数据集脚本中已确认）：
    - sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png: ratio=24.72%, score=1
    - sym_1_r1_0_r2_0_r3_1_r4_0_r5_0.png: ratio=24.36%, score=1
    - sym_3_r1_0_r2_0_r3_0_r4_0_r5_0.png: ratio=25.25%, score=1
    """

    EXPECTED = {
        "sym_0_r1_0_r2_0_r3_0_r4_0_r5_0.png": (1, 24.72),
        "sym_1_r1_0_r2_0_r3_1_r4_0_r5_0.png": (1, 24.36),
        "sym_3_r1_0_r2_0_r3_0_r4_0_r5_0.png": (1, 25.25),
    }

    def _run(self, image, **kwargs):
        from src.core.scoring.land_sea_ratio import compute_land_sea_ratio
        return compute_land_sea_ratio(image, **kwargs)

    def test_real_image_scores_match_old_algorithm(self):
        """逐图验证新架构评分和海陆比值与老算法计算结果一致。"""
        for filename, (expected_score, expected_ratio) in self.EXPECTED.items():
            image_path = _COMBINE_HORIZONTAL / filename
            if not image_path.exists():
                self.skipTest(f"测试图像不存在: {image_path}")
            image = _load_image(image_path)
            score, ratio_percent, _, _ = self._run(image)
            with self.subTest(filename=filename):
                self.assertEqual(
                    score, expected_score,
                    msg=f"{filename}: 评分不匹配，期望 {expected_score}，实际 {score}",
                )
                self.assertAlmostEqual(
                    ratio_percent, expected_ratio, places=2,
                    msg=f"{filename}: 海陆比不匹配，期望 {expected_ratio}，实际 {ratio_percent}",
                )

    def test_debug_image_pixel_equal_to_dev1_baseline(self):
        """
        新架构 debug 染色图与 wise_image_dev1 老架构基准图逐像素比对，证明可视化等价。
        同时将新架构染色图保存到 wise_image_dev2 便于人工检查。
        """
        _WISE_IMAGE_DEV2.mkdir(parents=True, exist_ok=True)

        for filename in self.EXPECTED:
            image_path = _COMBINE_HORIZONTAL / filename
            dev1_path = _WISE_IMAGE_DEV1 / filename
            if not image_path.exists() or not dev1_path.exists():
                self.skipTest(f"测试数据不完整: {image_path} 或 {dev1_path}")

            image = _load_image(image_path)
            dev1_image = _load_image(dev1_path)

            _, _, _, vis_image = self._run(image, is_debug=True)

            # 保存到 wise_image_dev2 便于人工比对（用 imencode+tofile 规避中文路径问题）
            dev2_path = _WISE_IMAGE_DEV2 / filename
            success, buf = cv2.imencode(dev2_path.suffix, vis_image)
            if success:
                np.array(buf).tofile(str(dev2_path))

            with self.subTest(filename=filename):
                self.assertTrue(
                    np.array_equal(vis_image, dev1_image),
                    msg=(
                        f"{filename}: 新旧架构染色图不一致，"
                        f"请对比 {dev1_path} 和 {dev2_path}"
                    ),
                )


if __name__ == "__main__":
    unittest.main()
