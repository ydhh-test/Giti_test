import pytest
from src.models.tire_struct import TireStruct
from src.models.image_models import SmallImage, BigImage
from src.models.enums import ImageModeEnum, ImageFormatEnum

# ===================== 测试数据（模块级常量）=====================

META_DICT = {
    "width": 512,
    "height": 512,
    "channels": 3,
    "mode": "RGB",
    "format": "png",
    "size": 10000
}

SMALL_IMAGE_DICT = {
    "image_base64": "data:image/png;base64,iVBORw0KGgo=",
    "meta": META_DICT,
    "biz": {"level": "small", "region": "side", "source_type": "original"}
}

BIG_IMAGE_DICT = {
    "image_base64": "data:image/png;base64,iVBORw0KGgo=",
    "meta": {"width": 1024, "height": 512, "channels": 3, "mode": "RGB", "format": "png", "size": 20000},
    "biz": {"level": "big", "source_type": "concat"}
}


# ===================== 校验规则测试 =====================

class TestTireStructValidation:
    """TireStruct 校验规则测试"""

    def test_validate_images_required_with_small(self):
        """✅ 校验规则 1：有小图"""
        input_dict = {"small_images": [SMALL_IMAGE_DICT], "rules_config": []}
        expected_dict = {"small_images_count": 1}

        tire = TireStruct.model_validate(input_dict)
        assert len(tire.small_images) == expected_dict["small_images_count"]

    def test_validate_images_required_with_big(self):
        """✅ 校验规则 1：有大图"""
        input_dict = {"small_images": [], "big_image": BIG_IMAGE_DICT, "rules_config": []}
        expected_dict = {"has_big_image": True}

        tire = TireStruct.model_validate(input_dict)
        assert (tire.big_image is not None) == expected_dict["has_big_image"]

    def test_validate_images_required_with_both(self):
        """✅ 校验规则 1：同时有小图和大图"""
        input_dict = {"small_images": [SMALL_IMAGE_DICT], "big_image": BIG_IMAGE_DICT, "rules_config": []}
        expected_dict = {"small_images_count": 1, "has_big_image": True}

        tire = TireStruct.model_validate(input_dict)
        assert len(tire.small_images) == expected_dict["small_images_count"]
        assert (tire.big_image is not None) == expected_dict["has_big_image"]

    def test_validate_images_required_error(self):
        """❌ 校验规则 1：小图和大图都为空"""
        input_dict = {"small_images": [], "big_image": None, "rules_config": []}

        with pytest.raises(ValueError, match="必须输入小图或大图"):
            TireStruct.model_validate(input_dict)

    def test_validate_scheme_rank_valid(self):
        """✅ 校验规则 2：scheme_rank = 1"""
        input_dict = {"small_images": [SMALL_IMAGE_DICT], "rules_config": [], "scheme_rank": 1}
        expected_dict = {"scheme_rank": 1}

        tire = TireStruct.model_validate(input_dict)
        assert tire.scheme_rank == expected_dict["scheme_rank"]

    def test_validate_scheme_rank_large(self):
        """✅ 校验规则 2：scheme_rank = 100"""
        input_dict = {"small_images": [SMALL_IMAGE_DICT], "rules_config": [], "scheme_rank": 100}
        expected_dict = {"scheme_rank": 100}

        tire = TireStruct.model_validate(input_dict)
        assert tire.scheme_rank == expected_dict["scheme_rank"]

    def test_validate_scheme_rank_error(self):
        """❌ 校验规则 2：scheme_rank = 0"""
        input_dict = {"small_images": [SMALL_IMAGE_DICT], "rules_config": [], "scheme_rank": 0}

        with pytest.raises(ValueError, match="方案排名必须>=1"):
            TireStruct.model_validate(input_dict)

    def test_validate_scheme_rank_negative(self):
        """❌ 校验规则 2：scheme_rank = -1"""
        input_dict = {"small_images": [SMALL_IMAGE_DICT], "rules_config": [], "scheme_rank": -1}

        with pytest.raises(ValueError, match="方案排名必须>=1"):
            TireStruct.model_validate(input_dict)


# ===================== 可变性测试 =====================

class TestTireStructMutability:
    """TireStruct 可变性测试（validate_assignment=True）"""

    def test_runtime_modification(self):
        """运行时修改字段"""
        input_dict = {"small_images": [SMALL_IMAGE_DICT], "rules_config": []}
        expected_dict = {"flag": True, "err_msg": "执行成功", "scheme_rank": 5}

        tire = TireStruct.model_validate(input_dict)
        tire.flag = expected_dict["flag"]
        tire.err_msg = expected_dict["err_msg"]
        tire.scheme_rank = expected_dict["scheme_rank"]

        assert tire.flag == expected_dict["flag"]
        assert tire.err_msg == expected_dict["err_msg"]
        assert tire.scheme_rank == expected_dict["scheme_rank"]

    def test_runtime_validation(self):
        """运行时修改为非法值触发校验"""
        input_dict = {"small_images": [SMALL_IMAGE_DICT], "rules_config": [], "scheme_rank": 1}

        tire = TireStruct.model_validate(input_dict)
        with pytest.raises(ValueError):
            tire.scheme_rank = 0


# ===================== 深度序列化测试 =====================

class TestTireStructDeepSerialization:
    """TireStruct 深度序列化/反序列化测试"""

    def test_deep_serialization(self):
        """测试深度序列化/反序列化"""
        input_dict = {"small_images": [SMALL_IMAGE_DICT], "rules_config": []}
        expected_dict = {"width": 512, "region": "side"}

        # 反序列化：dict → TireStruct → SmallImage → ImageMeta/ImageBiz
        tire = TireStruct.model_validate(input_dict)

        # 验证嵌套对象（右侧从 expected_dict 取）
        assert tire.small_images[0].meta.width == expected_dict["width"]
        assert tire.small_images[0].biz.region.value == expected_dict["region"]

        # 序列化：TireStruct → SmallImage → ImageMeta/ImageBiz → dict
        output_dict = tire.model_dump()

        # 验证深度序列化结果（右侧从 expected_dict 取）
        assert output_dict["small_images"][0]["meta"]["width"] == expected_dict["width"]
        assert output_dict["small_images"][0]["biz"]["region"] == expected_dict["region"]


class TestTireStructDeepSerializationNegative:
    """TireStruct 深度反序列化反例测试"""

    def test_deep_invalid_small_image_base64(self):
        """❌ 小图 base64 格式错误"""
        input_dict = {"small_images": [{**SMALL_IMAGE_DICT, "image_base64": "invalid"}], "rules_config": []}

        with pytest.raises(ValueError, match="image_base64必须包含data:image"):
            TireStruct.model_validate(input_dict)

    def test_deep_invalid_meta_width_zero(self):
        """❌ ImageMeta width = 0"""
        input_dict = {"small_images": [{**SMALL_IMAGE_DICT, "meta": {**META_DICT, "width": 0}}], "rules_config": []}

        with pytest.raises(ValueError):
            TireStruct.model_validate(input_dict)

    def test_deep_invalid_biz_region_none(self):
        """❌ ImageBiz 原始数据缺少 region"""
        input_dict = {"small_images": [{**SMALL_IMAGE_DICT, "biz": {"level": "small", "region": None, "source_type": "original"}}], "rules_config": []}

        with pytest.raises(ValueError, match="原始数据必须指定region"):
            TireStruct.model_validate(input_dict)

    def test_deep_invalid_meta_channels_over(self):
        """❌ ImageMeta channels = 5"""
        input_dict = {"small_images": [{**SMALL_IMAGE_DICT, "meta": {**META_DICT, "channels": 5}}], "rules_config": []}

        with pytest.raises(ValueError):
            TireStruct.model_validate(input_dict)

    def test_deep_invalid_meta_dimensions_over(self):
        """❌ ImageMeta width = 10001"""
        input_dict = {"small_images": [{**SMALL_IMAGE_DICT, "meta": {**META_DICT, "width": 10001}}], "rules_config": []}

        with pytest.raises(ValueError, match="图像尺寸超过上限"):
            TireStruct.model_validate(input_dict)
