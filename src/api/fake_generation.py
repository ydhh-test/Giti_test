from __future__ import annotations

from ..common.exceptions import InputTypeError, RuntimeProcessError
from ..models.fake_image_models import FakeBigImage, FakeBigImageBiz, FakeImageMeta
from ..models.fake_result_models import (
    FakeEvaluation,
    FakeFeatureResult,
    FakeLineage,
    FakeScoreResult,
)
from ..models.fake_tire_struct import FakeTireStruct


def generate_big_image_with_evaluation(tire_struct: FakeTireStruct) -> FakeTireStruct:
    """Fake API: 根据小图生成大图并返回评分结果。"""
    if not isinstance(tire_struct, FakeTireStruct):
        raise InputTypeError(
            function="generate_big_image_with_evaluation",
            param="tire_struct",
            expected_type="FakeTireStruct",
            actual_type=type(tire_struct).__name__,
        )

    err_msg = tire_struct.validate_request()
    if err_msg is not None:
        return create_error_response(tire_struct, "DATA_ERROR", err_msg)

    try:
        return create_success_response(tire_struct)
    except Exception as error:
        runtime_error = RuntimeProcessError(
            stage="create_success_response",
            high_level_failure="failed to build fake big image",
            original_error=error,
        )
        return create_error_response(tire_struct, "RUNTIME_ERROR", str(runtime_error))


def create_error_response(original: FakeTireStruct, err_code: str, err_msg: str) -> FakeTireStruct:
    """构造失败响应对象。"""
    return FakeTireStruct.model_construct(
        small_images=original.small_images,
        big_image=None,
        rules_config=original.rules_config,
        scheme_rank=original.scheme_rank,
        is_debug=original.is_debug,
        flag=False,
        err_code=err_code,
        err_msg=err_msg,
    )


def create_success_response(original: FakeTireStruct) -> FakeTireStruct:
    """构造成功响应对象（fake 固定输出）。"""
    source_image_ids = [img.biz.image_id for img in original.small_images]

    big_image = FakeBigImage(
        image_base64="data:image/png;base64,FAKE_BIG_IMAGE_PLACEHOLDER",
        meta=FakeImageMeta(width=1024, height=512, channel=3),
        biz=FakeBigImageBiz(
            image_id="big-001",
            scheme_rank=original.scheme_rank,
            status="generated",
        ),
        evaluation=FakeEvaluation(
            features=[
                FakeFeatureResult(
                    rule_name="rule6-1",
                    feature_name="pattern_continuity",
                    feature_value="good",
                    description="图案连续性",
                ),
                FakeFeatureResult(
                    rule_name="rule8",
                    feature_name="groove_count",
                    feature_value="1",
                    description="横沟数量",
                ),
            ]
        ),
        scores=[
            FakeScoreResult(
                rule_name="rule6-1",
                description="图案连续性检测",
                score_value=8.0,
                score_max=original.rules_config.rule6_1.score,
                reason="连续性基本满足要求",
            ),
            FakeScoreResult(
                rule_name="rule8",
                description="横沟数量检测",
                score_value=4.0,
                score_max=original.rules_config.rule8.score,
                reason="横沟数量满足要求",
            ),
        ],
        lineage=FakeLineage(
            source_image_ids=source_image_ids,
            scheme_rank=original.scheme_rank,
            summary=f"由 {len(source_image_ids)} 张小图按第 {original.scheme_rank} 名方案生成大图",
        ),
    )

    return FakeTireStruct.model_construct(
        small_images=original.small_images,
        big_image=big_image,
        rules_config=original.rules_config,
        scheme_rank=original.scheme_rank,
        is_debug=original.is_debug,
        flag=True,
        err_code=None,
        err_msg=None,
    )
