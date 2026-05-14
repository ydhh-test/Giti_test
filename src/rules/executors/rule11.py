from __future__ import annotations

from src.common.exceptions import InputDataError, InputTypeError
from src.core.longitudinal_groove import detect_longitudinal_grooves
from src.models.enums import RegionEnum
from src.models.image_models import BaseImage, SmallImage
from src.models.rule_models import BaseRuleFeature, BaseRuleScore, Rule11Config, Rule11Feature, Rule11Score
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor
from src.utils.image_utils import base64_to_ndarray


FEATURE_FUNCTION = "Rule11Executor.exec_feature"
SCORE_FUNCTION = "Rule11Executor.exec_score"


@register_rule_executor
class Rule11Executor(RuleExecutor):
    rule_cls = Rule11Config

    def exec_feature(
        self,
        image: BaseImage,
        config: Rule11Config,
    ) -> BaseRuleFeature:
        if not isinstance(image, SmallImage):
            raise InputTypeError(FEATURE_FUNCTION, "image", "SmallImage", type(image).__name__)
        if not isinstance(config, Rule11Config):
            raise InputTypeError(FEATURE_FUNCTION, "config", "Rule11Config", type(config).__name__)

        region = image.biz.region
        if region not in (RegionEnum.CENTER, RegionEnum.SIDE):
            raise InputDataError(FEATURE_FUNCTION, "image.biz.region", "must be center or side", region)

        image_array = base64_to_ndarray(image.image_base64)
        image_height, image_width = image_array.shape[:2]

        groove_count, _positions, _widths, _line_mask, _debug_image = detect_longitudinal_grooves(
            image_array,
            nominal_width_px=config.groove_width,
            min_width_px=_calculate_min_width_px(config),
            edge_margin_px=_ratio_to_px(config.edge_margin_ratio, image_width, minimum=0),
            min_segment_length_px=_ratio_to_px(config.min_segment_length_ratio, image_height, minimum=1),
            max_angle_deg=config.max_angle_from_vertical,
        )

        return Rule11Feature(
            num_longitudinal_grooves=groove_count,
            region=region,
        )

    def exec_score(
        self,
        config: Rule11Config,
        feature: Rule11Feature,
    ) -> BaseRuleScore:
        if not isinstance(config, Rule11Config):
            raise InputTypeError(SCORE_FUNCTION, "config", "Rule11Config", type(config).__name__)
        if not isinstance(feature, Rule11Feature):
            raise InputTypeError(SCORE_FUNCTION, "feature", "Rule11Feature", type(feature).__name__)

        if feature.region == RegionEnum.CENTER:
            max_count = config.max_count_center
        elif feature.region == RegionEnum.SIDE:
            max_count = config.max_count_side
        else:
            raise InputDataError(SCORE_FUNCTION, "feature.region", "must be center or side", feature.region)

        score = config.max_score if feature.num_longitudinal_grooves <= max_count else 0
        return Rule11Score(score=score)


def _calculate_min_width_px(config: Rule11Config) -> int:
    return max(1, int(round(config.groove_width - config.min_width_offset_px)))


def _ratio_to_px(ratio: float, reference_px: int, *, minimum: int) -> int:
    return max(minimum, int(round(reference_px * ratio)))
