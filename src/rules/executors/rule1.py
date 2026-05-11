from src.models.rule_models import Rule1Config
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule1Executor(RuleExecutor):
    rule_cls = Rule1Config
