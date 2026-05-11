import pytest

from src.models.enums import ImageFormatEnum, ImageModeEnum, LevelEnum, RegionEnum
from src.models.image_models import BigImage, ImageBiz, ImageMeta
from src.models.rule_models import Rule1Config
from src.rules.base import RuleExecutor


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


def test_rule_executor_defaults_raise_not_implemented():
    """验证 RuleExecutor 默认 feature 和 score 方法在未实现时抛出 NotImplementedError。"""

    class UnimplementedExecutor(RuleExecutor):
        rule_cls = Rule1Config

    executor = UnimplementedExecutor()
    config = Rule1Config()

    with pytest.raises(NotImplementedError, match="rule1.exec_feature"):
        executor.exec_feature(make_big_image(), config)
    with pytest.raises(NotImplementedError, match="rule1.exec_score"):
        executor.exec_score(config, feature=None)

