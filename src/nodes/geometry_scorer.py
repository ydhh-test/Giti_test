"""几何评分节点。

本节点基于大图中已存在的规则 feature 重新计算规则得分，并刷新图片
总分。它适用于用户调整 ``rules_config`` 中的阈值或参数后，复用已有
feature 重新评分的场景。
"""

from __future__ import annotations

from src.common.exceptions import InputDataError
from src.models.image_models import BigImage
from src.models.rule_models import BaseRuleConfig
from src.nodes.base import GEOMETRY_SCORER_CONFIGS, RuleRunner, recalculate_current_score, select_node_configs


NODE_NAME = "geometry_scorer"


def score_geometry(
    big_image: BigImage | None,
    rules_config: list[BaseRuleConfig],
    recalculate_rule_scores: bool = True,
) -> BigImage:
    """基于已有 feature 重新计算规则得分并刷新总分。

    当 ``recalculate_rule_scores`` 为 ``True`` 时，函数会从
    ``rules_config`` 中筛选本节点支持的规则配置，逐条找到大图
    ``evaluation`` 中对应的 ``RuleEvaluation``，使用已有 feature 重新
    计算 score，并同步更新该 ``RuleEvaluation`` 的 config 和 score。

    当 ``recalculate_rule_scores`` 为 ``False`` 时，函数不会重新计算
    每条规则的 score，只会根据已有 score 汇总刷新 ``current_score``。

    Args:
        big_image: 已完成大图 feature 计算的大图对象。不能为 ``None``，
            且必须已经存在 ``evaluation``。
        rules_config: 用户传入的完整规则配置列表，函数只会处理本节点
            支持的规则配置。
        recalculate_rule_scores: 是否逐条重新计算规则得分。默认为
            ``True``；传入 ``False`` 时只刷新总分。

    Returns:
        原始 ``big_image`` 对象。函数会原地更新其中的 ``RuleEvaluation``
        和 ``evaluation.current_score``。

    Raises:
        InputDataError: 当 ``big_image``、``big_image.evaluation``、目标
            ``RuleEvaluation`` 或目标 feature 缺失时抛出；规则配置重复
            时也会抛出该异常。
        Exception: 规则执行过程中的异常不会在节点内捕获，会原样向上透传。
    """

    if big_image is None:
        raise InputDataError(NODE_NAME, "big_image", "big_image is required")
    if big_image.evaluation is None:
        raise InputDataError(
            NODE_NAME,
            "big_image.evaluation",
            "big_image.evaluation is required",
        )

    evaluation = big_image.evaluation

    if recalculate_rule_scores:
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
