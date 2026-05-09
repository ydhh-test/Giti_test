from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from src.models.image_models import BaseImage, BigImage
from src.models.rule_models import BaseRuleConfig, BaseRuleFeature, BaseRuleScore


class RuleExecutor(ABC):
    """所有规则执行器的基类。

    子类必须通过 ``rule_cls`` 绑定对应的规则配置类。
    注册器会从该配置类推导对外规则名，推导规则与
    ``BaseRuleConfig.name`` 保持一致。
    """

    rule_cls: ClassVar[type[BaseRuleConfig]]

    @abstractmethod
    def exec_feature(
        self,
        image: BaseImage,
        config: BaseRuleConfig,
    ) -> BaseRuleFeature:
        ...

    @abstractmethod
    def exec_score(
        self,
        config: BaseRuleConfig,
        feature: BaseRuleFeature,
    ) -> BaseRuleScore:
        ...

    def exec_image_operation(
        self,
        image: BaseImage,
        config: BaseRuleConfig,
    ) -> BigImage:
        """可选的图片操作钩子。

        只做 feature / score 的规则不需要覆盖该方法。
        图片操作类规则，例如 rule19，覆盖该方法并返回新的 BigImage。
        返回值仍由节点层负责写回到业务状态中。
        """

        raise NotImplementedError("exec_image_operation is not implemented")
