from src.models.rule_models import Rule8Config
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule8Executor(RuleExecutor):
    rule_cls = Rule8Config
