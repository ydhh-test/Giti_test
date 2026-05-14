from __future__ import annotations

from src.models.image_models import BaseImage
from src.models.rule_models import Rule6Config, Rule6Feature, Rule6Score
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule6Executor(RuleExecutor):
    rule_cls = Rule6Config

    def exec_feature(
        self,
        image: BaseImage,
        config: Rule6Config,
    ) -> Rule6Feature:
        import cv2
        from src.core.detection.pattern_continuity import detect_pattern_continuity
        from src.utils.image_utils import base64_to_ndarray, ndarray_to_base64

        bgr = base64_to_ndarray(image.image_base64)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        is_continuous, vis_name, vis_image = detect_pattern_continuity(
            gray,
            is_debug=config.is_debug,
        )

        vis_names = None
        vis_images = None
        if config.is_debug and vis_image is not None:
            vis_names = [vis_name]
            vis_images = [ndarray_to_base64(vis_image, image_type="png")]

        return Rule6Feature(
            is_continuous=is_continuous,
            vis_names=vis_names,
            vis_images=vis_images,
        )

    def exec_score(
        self,
        config: Rule6Config,
        feature: Rule6Feature,
    ) -> Rule6Score:
        score = config.max_score if feature.is_continuous else 0
        return Rule6Score(score=score)
