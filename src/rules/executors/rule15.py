from src.models.rule_models import Rule15Config
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule15Executor(RuleExecutor):
    rule_cls = Rule15Config
