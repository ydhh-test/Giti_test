import pytest

from src.models.enums import ImageFormatEnum, ImageModeEnum, LevelEnum, RegionEnum
from src.models.image_models import BigImage, ImageBiz, ImageMeta
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


def test_rule_executor_requires_feature_and_score_implementation():
    """验证 RuleExecutor 子类必须实现 exec_feature 和 exec_score。"""

    class MissingScoreExecutor(RuleExecutor):
        def exec_feature(self, image, config):
            raise AssertionError("not called")

    with pytest.raises(TypeError, match="abstract"):
        MissingScoreExecutor()


def test_rule_executor_image_operation_is_optional():
    """验证 RuleExecutor 默认不提供图片操作能力，未覆盖时会抛 NotImplementedError。"""

    class FeatureScoreOnlyExecutor(RuleExecutor):
        def exec_feature(self, image, config):
            raise AssertionError("not called")

        def exec_score(self, config, feature):
            raise AssertionError("not called")

    executor = FeatureScoreOnlyExecutor()

    with pytest.raises(NotImplementedError, match="exec_image_operation"):
        executor.exec_image_operation(make_big_image(), config=None)
