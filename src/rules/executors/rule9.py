from src.models.rule_models import Rule9Config
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule9Executor(RuleExecutor):
    rule_cls = Rule9Config
