from __future__ import annotations

from src.models.image_models import BaseImage, BigImage
from src.models.rule_models import BaseRuleConfig, BaseRuleFeature, BaseRuleScore
from src.rules.registry import get_rule_executor


class RuleRunner:
    """Dispatch rule execution by ``config.name``."""

    @staticmethod
    def exec_feature(
        image: BaseImage,
        config: BaseRuleConfig,
    ) -> BaseRuleFeature:
        executor = get_rule_executor(config.name)
        return executor.exec_feature(image, config)

    @staticmethod
    def exec_score(
        config: BaseRuleConfig,
        feature: BaseRuleFeature,
    ) -> BaseRuleScore:
        executor = get_rule_executor(config.name)
        return executor.exec_score(config, feature)

    @staticmethod
    def exec_image_operation(
        image: BaseImage,
        config: BaseRuleConfig,
    ) -> BigImage:
        executor = get_rule_executor(config.name)
        return executor.exec_image_operation(image, config)
