from src.models.rule_models import Rule17Config
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule17Executor(RuleExecutor):
    rule_cls = Rule17Config
