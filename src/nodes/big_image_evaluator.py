"""Big image evaluation node."""

from __future__ import annotations

from src.common.exceptions import InputDataError
from src.models.image_models import BigImage
from src.models.rule_models import BaseRuleConfig
from src.nodes.base import BIG_IMAGE_EVALUATOR_CONFIGS, evaluate_image_with_configs, select_node_configs


NODE_NAME = "big_image_evaluator"


def evaluate_big_image(
    big_image: BigImage | None,
    rules_config: list[BaseRuleConfig],
) -> BigImage:
    """Evaluate the single big image and write the evaluation back."""

    if big_image is None:
        raise InputDataError(NODE_NAME, "big_image", "big_image is required")

    configs = select_node_configs(
        rules_config,
        BIG_IMAGE_EVALUATOR_CONFIGS,
    )
    big_image.evaluation = evaluate_image_with_configs(
        big_image,
        configs,
    )

    return big_image
