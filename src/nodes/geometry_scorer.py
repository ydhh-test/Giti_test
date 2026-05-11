"""Geometry scoring node."""

from __future__ import annotations

from src.common.exceptions import InputDataError
from src.models.image_models import BigImage
from src.models.rule_models import BaseRuleConfig
from src.nodes.base import GEOMETRY_SCORER_CONFIGS, RuleRunner, recalculate_current_score, select_node_configs


NODE_NAME = "geometry_scorer"


def score_geometry(
    big_image: BigImage | None,
    rules_config: list[BaseRuleConfig],
) -> BigImage:
    """Recalculate geometry scores from existing big-image features."""

    if big_image is None:
        raise InputDataError(NODE_NAME, "big_image", "big_image is required")
    if big_image.evaluation is None:
        raise InputDataError(
            NODE_NAME,
            "big_image.evaluation",
            "big_image.evaluation is required",
        )

    evaluation = big_image.evaluation
    configs = select_node_configs(
        rules_config,
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
    return big_image
