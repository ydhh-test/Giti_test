"""Big image evaluation node."""

from __future__ import annotations

from src.common.exceptions import InputDataError
from src.models.tire_struct import TireStruct
from src.nodes.base import BIG_IMAGE_EVALUATOR_CONFIGS, evaluate_image_with_configs, select_node_configs


NODE_NAME = "big_image_evaluator"


def evaluate_big_image(tire_struct: TireStruct) -> TireStruct:
    """Evaluate the single big image and write the evaluation back."""

    if tire_struct.big_image is None:
        raise InputDataError(NODE_NAME, "big_image", "big_image is required")

    configs = select_node_configs(
        tire_struct.rules_config,
        BIG_IMAGE_EVALUATOR_CONFIGS,
    )
    tire_struct.big_image.evaluation = evaluate_image_with_configs(
        tire_struct.big_image,
        configs,
    )

    tire_struct.flag = True
    tire_struct.err_msg = None
    return tire_struct
