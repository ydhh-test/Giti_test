from src.models.rule_models import Rule7Config
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule7Executor(RuleExecutor):
    rule_cls = Rule7Config
