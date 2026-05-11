from src.models.rule_models import Rule14Config
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule14Executor(RuleExecutor):
    rule_cls = Rule14Config
