"""Small image evaluation node."""

from __future__ import annotations

from src.common.exceptions import InputDataError
from src.models.tire_struct import TireStruct
from src.nodes.base import SMALL_IMAGE_EVALUATOR_CONFIGS, evaluate_image_with_configs, select_node_configs


NODE_NAME = "small_image_evaluator"


def evaluate_small_images(tire_struct: TireStruct) -> TireStruct:
    """Evaluate each small image and write independent evaluations back."""

    if not tire_struct.small_images:
        raise InputDataError(NODE_NAME, "small_images", "small_images is required")

    configs = select_node_configs(
        tire_struct.rules_config,
        SMALL_IMAGE_EVALUATOR_CONFIGS,
    )

    for small_image in tire_struct.small_images:
        small_image.evaluation = evaluate_image_with_configs(
            small_image,
            configs,
        )

    tire_struct.flag = True
    tire_struct.err_msg = None
    return tire_struct
