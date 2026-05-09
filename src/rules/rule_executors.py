from __future__ import annotations

from src.models.enums import LevelEnum
from src.models.image_models import BaseImage, BigImage
from src.models.rule_models import (
    BaseRuleConfig,
    BaseRuleFeature,
    BaseRuleScore,
    Rule1Config,
    Rule2Config,
    Rule3Config,
    Rule4Config,
    Rule5Config,
    Rule6AConfig,
    Rule6Config,
    Rule7Config,
    Rule8Config,
    Rule9Config,
    Rule10Config,
    Rule11Config,
    Rule12Config,
    Rule13Config,
    Rule14Config,
    Rule15Config,
    Rule16Config,
    Rule17Config,
    Rule18Config,
    Rule19Config,
    Rule19Feature,
    Rule19Score,
    Rule20Config,
    Rule21Config,
    Rule22Config,
)
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


class UnsupportedRuleExecutor(RuleExecutor):
    """暂未落地规则的默认执行器。

    这些 executor 先完成注册和规则绑定，但不提供真实 feature / score
    计算能力，也不定义图片操作能力。后续实现具体规则时，只需要在对应
    子类中覆盖相关方法。
    """

    def exec_feature(
        self,
        image: BaseImage,
        config: BaseRuleConfig,
    ) -> BaseRuleFeature:
        raise NotImplementedError(f"{config.name}.exec_feature is not implemented")

    def exec_score(
        self,
        config: BaseRuleConfig,
        feature: BaseRuleFeature,
    ) -> BaseRuleScore:
        raise NotImplementedError(f"{config.name}.exec_score is not implemented")


@register_rule_executor
class Rule1Executor(UnsupportedRuleExecutor):
    rule_cls = Rule1Config


@register_rule_executor
class Rule2Executor(UnsupportedRuleExecutor):
    rule_cls = Rule2Config


@register_rule_executor
class Rule3Executor(UnsupportedRuleExecutor):
    rule_cls = Rule3Config


@register_rule_executor
class Rule4Executor(UnsupportedRuleExecutor):
    rule_cls = Rule4Config


@register_rule_executor
class Rule5Executor(UnsupportedRuleExecutor):
    rule_cls = Rule5Config


@register_rule_executor
class Rule6Executor(UnsupportedRuleExecutor):
    rule_cls = Rule6Config


@register_rule_executor
class Rule6AExecutor(UnsupportedRuleExecutor):
    rule_cls = Rule6AConfig


@register_rule_executor
class Rule7Executor(UnsupportedRuleExecutor):
    rule_cls = Rule7Config


@register_rule_executor
class Rule8Executor(UnsupportedRuleExecutor):
    rule_cls = Rule8Config


@register_rule_executor
class Rule9Executor(UnsupportedRuleExecutor):
    rule_cls = Rule9Config


@register_rule_executor
class Rule10Executor(UnsupportedRuleExecutor):
    rule_cls = Rule10Config


@register_rule_executor
class Rule11Executor(UnsupportedRuleExecutor):
    rule_cls = Rule11Config


@register_rule_executor
class Rule12Executor(UnsupportedRuleExecutor):
    rule_cls = Rule12Config


@register_rule_executor
class Rule13Executor(UnsupportedRuleExecutor):
    rule_cls = Rule13Config


@register_rule_executor
class Rule14Executor(UnsupportedRuleExecutor):
    rule_cls = Rule14Config


@register_rule_executor
class Rule15Executor(UnsupportedRuleExecutor):
    rule_cls = Rule15Config


@register_rule_executor
class Rule16Executor(UnsupportedRuleExecutor):
    rule_cls = Rule16Config


@register_rule_executor
class Rule17Executor(UnsupportedRuleExecutor):
    rule_cls = Rule17Config


@register_rule_executor
class Rule18Executor(UnsupportedRuleExecutor):
    rule_cls = Rule18Config


@register_rule_executor
class Rule19Executor(RuleExecutor):
    rule_cls = Rule19Config

    def exec_feature(
        self,
        image: BaseImage,
        config: Rule19Config,
    ) -> BaseRuleFeature:
        return Rule19Feature()

    def exec_score(
        self,
        config: Rule19Config,
        feature: Rule19Feature,
    ) -> BaseRuleScore:
        return Rule19Score(score=0)

    def exec_image_operation(
        self,
        image: BaseImage,
        config: Rule19Config,
    ) -> BigImage:
        """添加装饰边框，并返回新的 BigImage。

        executor 只返回数据，不写回业务状态。
        返回的 BigImage 通常由节点层赋值给 ``tire_struct.big_image``。
        """

        if isinstance(image, BigImage):
            return image

        return BigImage(
            image_base64=image.image_base64,
            meta=image.meta,
            biz=image.biz.model_copy(update={"level": LevelEnum.BIG}),
            evaluation=image.evaluation,
        )


@register_rule_executor
class Rule20Executor(UnsupportedRuleExecutor):
    rule_cls = Rule20Config


@register_rule_executor
class Rule21Executor(UnsupportedRuleExecutor):
    rule_cls = Rule21Config


@register_rule_executor
class Rule22Executor(UnsupportedRuleExecutor):
    rule_cls = Rule22Config
