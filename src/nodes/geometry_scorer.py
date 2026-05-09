"""Geometry scoring node."""

from __future__ import annotations

from src.common.exceptions import InputDataError
from src.models.tire_struct import TireStruct
from src.nodes.base import GEOMETRY_SCORER_CONFIGS, RuleRunner, recalculate_current_score, select_node_configs


NODE_NAME = "geometry_scorer"


def score_geometry(tire_struct: TireStruct) -> TireStruct:
    """Recalculate geometry scores from existing big-image features."""

    if tire_struct.big_image is None:
        raise InputDataError(NODE_NAME, "big_image", "big_image is required")
    if tire_struct.big_image.evaluation is None:
        raise InputDataError(
            NODE_NAME,
            "big_image.evaluation",
            "big_image.evaluation is required",
        )

    evaluation = tire_struct.big_image.evaluation
    configs = select_node_configs(
        tire_struct.rules_config,
        GEOMETRY_SCORER_CONFIGS,
    )

    for config in configs:
        rule_evaluation = evaluation.get_rule(config.name)
        if rule_evaluation is None:
            raise InputDataError(
                NODE_NAME,
                f"big_image.evaluation.rules.{config.name}",
                f"missing rule evaluation for {config.name}",
            )
        if rule_evaluation.feature is None:
            raise InputDataError(
                NODE_NAME,
                f"big_image.evaluation.rules.{config.name}.feature",
                f"missing feature for {config.name}",
            )

        rule_evaluation.config = config
        rule_evaluation.score = RuleRunner.exec_score(config, rule_evaluation.feature)

    recalculate_current_score(evaluation)
    tire_struct.flag = True
    tire_struct.err_msg = None
    return tire_struct
