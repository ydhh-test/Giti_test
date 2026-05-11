from src.models.rule_models import Rule20Config
from src.rules.base import RuleExecutor
from src.rules.registry import register_rule_executor


@register_rule_executor
class Rule20Executor(RuleExecutor):
    rule_cls = Rule20Config
