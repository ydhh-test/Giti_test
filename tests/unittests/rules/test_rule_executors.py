import pytest

from src.models.enums import ImageFormatEnum, ImageModeEnum, LevelEnum, RegionEnum
from src.models.image_models import BigImage, ImageBiz, ImageMeta
from src.models.rule_models import (
    Rule1Config,
    Rule2Config,
    Rule3Config,
    Rule4Config,
    Rule5Config,
    Rule6AConfig,
    Rule6Config,
    Rule7Config,
    Rule8Config,
    Rule9Config,
    Rule10Config,
    Rule11Config,
    Rule12Config,
    Rule13Config,
    Rule14Config,
    Rule15Config,
    Rule16Config,
    Rule17Config,
    Rule18Config,
    Rule19Config,
    Rule20Config,
    Rule21Config,
    Rule22Config,
)
from src.rules.base import RuleExecutor
from src.rules.registry import get_rule_executor
from src.rules import rule_executors
from src.rules.rule_executors import Rule19Executor, UnsupportedRuleExecutor


ALL_RULE_CONFIGS = [
    Rule1Config,
    Rule2Config,
    Rule3Config,
    Rule4Config,
    Rule5Config,
    Rule6Config,
    Rule6AConfig,
    Rule7Config,
    Rule8Config,
    Rule9Config,
    Rule10Config,
    Rule11Config,
    Rule12Config,
    Rule13Config,
    Rule14Config,
    Rule15Config,
    Rule16Config,
    Rule17Config,
    Rule18Config,
    Rule19Config,
    Rule20Config,
    Rule21Config,
    Rule22Config,
]


def make_big_image() -> BigImage:
    return BigImage(
        image_base64="data:image/png;base64,original",
        meta=ImageMeta(
            width=100,
            height=40,
            channels=3,
            mode=ImageModeEnum.RGB,
            format=ImageFormatEnum.PNG,
            size=20,
        ),
        biz=ImageBiz(level=LevelEnum.BIG, region=RegionEnum.CENTER),
    )


def make_config() -> Rule19Config:
    return Rule19Config(
        tire_design_width=80,
        decoration_border_alpha=0.5,
        decoration_gray_color=128,
    )


def test_rule19_executor_has_no_rule_name_attribute():
    """验证 Rule19Executor 不再声明单独的 rule_name 属性。"""
    assert not hasattr(Rule19Executor(), "rule_name")


def test_rule19_executor_defines_rule_cls():
    """验证 Rule19Executor 通过 rule_cls 绑定 Rule19Config。"""
    assert Rule19Executor.rule_cls is Rule19Config


def test_rule19_executor_inherits_rule_executor():
    """验证 Rule19Executor 是 RuleExecutor 的具体实现类。"""
    assert isinstance(Rule19Executor(), RuleExecutor)


def test_all_rule_executors_are_registered():
    """验证 Rule1 到 Rule22 的 executor 都已按 config 名称注册。"""
    for config_cls in ALL_RULE_CONFIGS:
        rule_name = config_cls.__name__.lower().replace("config", "")

        executor = get_rule_executor(rule_name)

        assert isinstance(executor, RuleExecutor)
        assert executor.rule_cls is config_cls


def test_only_rule19_defines_image_operation():
    """验证当前只有 Rule19Executor 覆盖图片操作方法，其余规则仍是未落地 executor。"""
    for config_cls in ALL_RULE_CONFIGS:
        rule_name = config_cls.__name__.lower().replace("config", "")
        executor_cls_name = f"{config_cls.__name__.replace('Config', '')}Executor"
        executor_cls = getattr(rule_executors, executor_cls_name)

        if rule_name == "rule19":
            assert "exec_image_operation" in executor_cls.__dict__
        else:
            assert issubclass(executor_cls, UnsupportedRuleExecutor)
            assert "exec_image_operation" not in executor_cls.__dict__


def test_rule19_exec_image_operation_returns_big_image():
    """验证 Rule19Executor.exec_image_operation 直接返回 BigImage 且不改写图片内容。"""
    result = Rule19Executor().exec_image_operation(make_big_image(), make_config())

    assert isinstance(result, BigImage)
    assert result.biz.level == LevelEnum.BIG
    assert result.image_base64 == "data:image/png;base64,original"


def test_rule19_executor_is_registered_by_config_name():
    """验证可以通过 Rule19Config.name 从全局注册表取回 Rule19Executor。"""
    assert isinstance(get_rule_executor(make_config().name), Rule19Executor)
