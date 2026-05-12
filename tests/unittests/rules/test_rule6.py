# -*- coding: utf-8 -*-
"""
Rule6 执行器单元测试

测试目标：src.rules.executors.rule6.Rule6Executor

最重要的测试验证逻辑：
- 使用真实轮胎小图验证 exec_feature 的连续性判断与 feature/dev 老架构预期一致：
    center_inf/0.png → is_continuous=False
    center_inf/1.png → is_continuous=False
    center_inf/2.png → is_continuous=True
    side_inf/0.png   → is_continuous=True
- 验证 exec_score 在连续时返回 max_score，不连续时返回 0。
- 验证规则层与算法层的边界：exec_feature 只返回 Rule6Feature，
  不透传 vis_name / vis_image 等 debug 信息。

人工设计的覆盖性测试逻辑：
- 真实图 happy path：覆盖两个区域（center / side）和连续/不连续两种判断结果。
- exec_score 分支覆盖：is_continuous=True 和 is_continuous=False 两路。
- max_score 自定义：验证评分严格遵循 config.max_score，不硬编码默认值。
- 返回类型检查：验证 exec_feature 返回 Rule6Feature，exec_score 返回 Rule6Score。
- vis_names / vis_images 不泄露：非 debug 模式下 feature 不携带可视化数据。
"""

import pathlib
import unittest

try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False

_DATASET_BASE = pathlib.Path(__file__).parents[2] / "datasets" / "test_pattern_continuity"


# ============================================================
# exec_score 纯逻辑测试（不依赖 cv2 / 真实图片）
# ============================================================

class TestRule6ExecScore(unittest.TestCase):
    """
    Rule6Executor.exec_score 的纯逻辑测试，不依赖 cv2。

    只需要 Rule6Config、Rule6Feature、Rule6Score。
    """

    def _make_config(self, max_score: int = 10) -> "Rule6Config":
        from src.models.rule_models import Rule6Config
        return Rule6Config(max_score=max_score)

    def _make_feature(self, is_continuous: bool) -> "Rule6Feature":
        from src.models.rule_models import Rule6Feature
        return Rule6Feature(is_continuous=is_continuous)

    def test_exec_score_continuous_returns_max_score(self):
        """连续时评分应等于 config.max_score"""
        from src.rules.executors.rule6 import Rule6Executor
        executor = Rule6Executor()
        config = self._make_config(max_score=10)
        feature = self._make_feature(is_continuous=True)

        rst = executor.exec_score(config, feature)

        expected = 10
        self.assertEqual(rst.score, expected)

    def test_exec_score_discontinuous_returns_zero(self):
        """不连续时评分应为 0"""
        from src.rules.executors.rule6 import Rule6Executor
        executor = Rule6Executor()
        config = self._make_config(max_score=10)
        feature = self._make_feature(is_continuous=False)

        rst = executor.exec_score(config, feature)

        expected = 0
        self.assertEqual(rst.score, expected)

    def test_exec_score_respects_custom_max_score(self):
        """评分应严格按 config.max_score 计算，不硬编码"""
        from src.rules.executors.rule6 import Rule6Executor
        executor = Rule6Executor()
        config = self._make_config(max_score=5)
        feature = self._make_feature(is_continuous=True)

        rst = executor.exec_score(config, feature)

        expected = 5
        self.assertEqual(rst.score, expected)

    def test_exec_score_returns_rule6score_type(self):
        """exec_score 应返回 Rule6Score 实例"""
        from src.models.rule_models import Rule6Score
        from src.rules.executors.rule6 import Rule6Executor
        executor = Rule6Executor()
        config = self._make_config()
        feature = self._make_feature(is_continuous=True)

        rst = executor.exec_score(config, feature)

        self.assertIsInstance(rst, Rule6Score)


# ============================================================
# exec_feature 真实图片测试（依赖 cv2）
# ============================================================

@unittest.skipUnless(_HAS_CV2, "需要 cv2 和 numpy")
class TestRule6ExecFeatureWithRealImages(unittest.TestCase):
    """
    使用真实轮胎小图验证 exec_feature 的连续性判断结果。

    基准（来自 feature/dev 老架构验证）：
        center_inf/0.png → False
        center_inf/1.png → False
        center_inf/2.png → True
        side_inf/0.png   → True
    """

    def _load_small_image(self, image_path: pathlib.Path, region: str):
        """从磁盘加载图片并构造 SmallImage（base64 编码）。

        使用 cv2.imdecode 读取字节以兼容含非 ASCII 字符的路径。
        """
        from src.models.enums import (
            ImageFormatEnum, ImageModeEnum, LevelEnum, RegionEnum
        )
        from src.models.image_models import ImageBiz, ImageMeta, SmallImage
        from src.utils.image_utils import ndarray_to_base64

        img_bytes = np.frombuffer(image_path.read_bytes(), dtype=np.uint8)
        bgr = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        self.assertIsNotNone(bgr, f"图片读取失败：{image_path}")

        h, w, c = bgr.shape
        region_enum = RegionEnum.CENTER if region == "center" else RegionEnum.SIDE
        return SmallImage(
            image_base64=ndarray_to_base64(bgr, image_type="png"),
            meta=ImageMeta(
                width=w,
                height=h,
                channels=c,
                mode=ImageModeEnum.RGB,
                format=ImageFormatEnum.PNG,
                size=0,
            ),
            biz=ImageBiz(level=LevelEnum.SMALL, region=region_enum),
        )

    def _make_config(self):
        from src.models.rule_models import Rule6Config
        return Rule6Config()

    def test_exec_feature_center_inf_0_is_not_continuous(self):
        """center_inf/0.png 应判断为不连续"""
        from src.rules.executors.rule6 import Rule6Executor
        image = self._load_small_image(
            _DATASET_BASE / "center_inf" / "0.png", region="center"
        )
        config = self._make_config()
        executor = Rule6Executor()

        rst = executor.exec_feature(image, config)

        expected_is_continuous = False
        self.assertEqual(rst.is_continuous, expected_is_continuous)

    def test_exec_feature_center_inf_1_is_not_continuous(self):
        """center_inf/1.png 应判断为不连续"""
        from src.rules.executors.rule6 import Rule6Executor
        image = self._load_small_image(
            _DATASET_BASE / "center_inf" / "1.png", region="center"
        )
        config = self._make_config()
        executor = Rule6Executor()

        rst = executor.exec_feature(image, config)

        expected_is_continuous = False
        self.assertEqual(rst.is_continuous, expected_is_continuous)

    def test_exec_feature_center_inf_2_is_continuous(self):
        """center_inf/2.png 应判断为连续"""
        from src.rules.executors.rule6 import Rule6Executor
        image = self._load_small_image(
            _DATASET_BASE / "center_inf" / "2.png", region="center"
        )
        config = self._make_config()
        executor = Rule6Executor()

        rst = executor.exec_feature(image, config)

        expected_is_continuous = True
        self.assertEqual(rst.is_continuous, expected_is_continuous)

    def test_exec_feature_side_inf_0_is_continuous(self):
        """side_inf/0.png 应判断为连续"""
        from src.rules.executors.rule6 import Rule6Executor
        image = self._load_small_image(
            _DATASET_BASE / "side_inf" / "0.png", region="side"
        )
        config = self._make_config()
        executor = Rule6Executor()

        rst = executor.exec_feature(image, config)

        expected_is_continuous = True
        self.assertEqual(rst.is_continuous, expected_is_continuous)

    def test_exec_feature_returns_rule6feature_type(self):
        """exec_feature 应返回 Rule6Feature 实例"""
        from src.models.rule_models import Rule6Feature
        from src.rules.executors.rule6 import Rule6Executor
        image = self._load_small_image(
            _DATASET_BASE / "center_inf" / "2.png", region="center"
        )
        config = self._make_config()
        executor = Rule6Executor()

        rst = executor.exec_feature(image, config)

        self.assertIsInstance(rst, Rule6Feature)

    def test_exec_feature_does_not_leak_vis_data(self):
        """exec_feature 不应透传 vis_names / vis_images（非 debug 模式）"""
        from src.rules.executors.rule6 import Rule6Executor
        image = self._load_small_image(
            _DATASET_BASE / "center_inf" / "2.png", region="center"
        )
        config = self._make_config()
        executor = Rule6Executor()

        rst = executor.exec_feature(image, config)

        self.assertIsNone(rst.vis_names)
        self.assertIsNone(rst.vis_images)


if __name__ == "__main__":
    unittest.main()
