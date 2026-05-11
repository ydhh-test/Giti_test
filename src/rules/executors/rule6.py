from src.models.rule_models import Rule6Config
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule6Executor(RuleExecutor):
    rule_cls = Rule6Config
