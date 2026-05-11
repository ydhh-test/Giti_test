from __future__ import annotations

from src.common.exceptions import InputDataError
from src.models.image_models import BaseImage, ImageEvaluation, RuleEvaluation
from src.models.rule_models import (
    BaseRuleConfig,
    Rule1Config,
    Rule2Config,
    Rule3Config,
    Rule4Config,
    Rule5Config,
    Rule6AConfig,
    Rule6Config,
    Rule7Config,
    Rule8Config,
    Rule11Config,
    Rule12Config,
    Rule13Config,
    Rule14Config,
    Rule15Config,
    Rule16Config,
    Rule17Config,
    Rule18Config,
    Rule19Config,
    Rule21Config,
    Rule22Config,
)
from src.rules.runner import RuleRunner


SMALL_IMAGE_EVALUATOR_CONFIGS: list[type[BaseRuleConfig]] = [
    Rule6Config,
    Rule11Config,
]

STITCH_SCHEME_GENERATOR_CONFIGS: list[type[BaseRuleConfig]] = [
    Rule1Config,
    Rule2Config,
    Rule3Config,
    Rule4Config,
    Rule5Config,
    Rule6AConfig,
    Rule7Config,
    Rule12Config,
    Rule16Config,
    Rule17Config,
    Rule19Config,
]

BIG_IMAGE_EVALUATOR_CONFIGS: list[type[BaseRuleConfig]] = [
    Rule8Config,
    Rule13Config,
    Rule14Config,
    Rule15Config,
    Rule18Config,
    Rule21Config,
    Rule22Config,
]

GEOMETRY_SCORER_CONFIGS: list[type[BaseRuleConfig]] = [
    Rule8Config,
    Rule13Config,
    Rule14Config,
    Rule15Config,
    Rule18Config,
    Rule21Config,
    Rule22Config,
]


def validate_no_duplicate_config_types(configs: list[BaseRuleConfig]) -> None:
    seen: set[type[BaseRuleConfig]] = set()
    for config in configs:
        config_type = type(config)
        if config_type in seen:
            raise InputDataError(
                "rules_config",
                config.name,
                "duplicate rule config",
            )
        seen.add(config_type)


def select_node_configs(
    rules_config: list[BaseRuleConfig],
    ordered_config_types: list[type[BaseRuleConfig]],
) -> list[BaseRuleConfig]:
    validate_no_duplicate_config_types(rules_config)
    config_by_type = {type(config): config for config in rules_config}

    return [
        config_by_type[config_type]
        for config_type in ordered_config_types
        if config_type in config_by_type
    ]


def recalculate_current_score(evaluation: ImageEvaluation) -> None:
    evaluation.current_score = sum(
        rule.score.score for rule in evaluation.rules
        if rule.score is not None
    )


def evaluate_image_with_configs(
    image: BaseImage,
    configs: list[BaseRuleConfig],
) -> ImageEvaluation:
    rule_evaluations: list[RuleEvaluation] = []

    for config in configs:
        feature = RuleRunner.exec_feature(image, config)
        score = RuleRunner.exec_score(config, feature)
        rule_evaluations.append(
            RuleEvaluation(
                name=config.name,
                config=config,
                feature=feature,
                score=score,
            )
        )

    evaluation = ImageEvaluation(rules=rule_evaluations)
    recalculate_current_score(evaluation)
    return evaluation
