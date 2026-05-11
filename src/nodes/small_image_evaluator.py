"""Small image evaluation node."""

from __future__ import annotations

from src.common.exceptions import InputDataError
from src.models.image_models import SmallImage
from src.models.rule_models import BaseRuleConfig
from src.nodes.base import SMALL_IMAGE_EVALUATOR_CONFIGS, evaluate_image_with_configs, select_node_configs


NODE_NAME = "small_image_evaluator"


def evaluate_small_images(
    small_images: list[SmallImage],
    rules_config: list[BaseRuleConfig],
) -> list[SmallImage]:
    """Evaluate each small image and write independent evaluations back."""

    if not small_images:
        raise InputDataError(NODE_NAME, "small_images", "small_images is required")

    configs = select_node_configs(
        rules_config,
        SMALL_IMAGE_EVALUATOR_CONFIGS,
    )

    for small_image in small_images:
        small_image.evaluation = evaluate_image_with_configs(
            small_image,
            configs,
        )

    return small_images
