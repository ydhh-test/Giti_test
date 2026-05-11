from src.models.rule_models import Rule18Config
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule18Executor(RuleExecutor):
    rule_cls = Rule18Config
