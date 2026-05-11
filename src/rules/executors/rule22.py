from src.models.rule_models import Rule22Config
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule22Executor(RuleExecutor):
    rule_cls = Rule22Config
