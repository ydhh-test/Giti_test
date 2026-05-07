import pytest
from src.models.scheme_models import RibTemplate, Symmetry0, RibSchemeImpl, DecorationImpl


# ===================== 模板类 frozen 测试 =====================

class TestTemplateFrozen:
    """模板类 frozen 测试"""

    def test_rib_template_frozen(self):
        """RibTemplate 不可修改"""
        input_dict = {"region": "side", "operation_template": [""], "rib_name": "rib1"}

        rib = RibTemplate.model_validate(input_dict)
        with pytest.raises(Exception):
            rib.region = "center"

    def test_symmetry0_frozen(self):
        """Symmetry0 不可修改"""
        template = Symmetry0()
        with pytest.raises(Exception):
            template.rib_number = 10


# ===================== RibSchemeImpl 校验规则测试 =====================

class TestRibSchemeImplValidation:
    """RibSchemeImpl 校验规则测试"""

    def test_validate_name_required_top_level_with_name(self):
        """✅ 校验规则 11：最外层有 rib_name"""
        input_dict = {"source_type": "original", "operations": [""], "rib_name": "rib1", "is_nested": False}
        expected_dict = {"rib_name": "rib1"}

        rib = RibSchemeImpl.model_validate(input_dict)
        assert rib.rib_name == expected_dict["rib_name"]

    def test_validate_name_required_top_level_without_name(self):
        """❌ 校验规则 11：最外层没有 rib_name"""
        input_dict = {"source_type": "original", "operations": [""], "is_nested": False}

        with pytest.raises(ValueError, match="最外层RIB必须有rib_name"):
            RibSchemeImpl.model_validate(input_dict)

    def test_validate_name_nested_without_name(self):
        """✅ 校验规则 11：嵌套 RIB 可以没有 rib_name"""
        input_dict = {"source_type": "original", "operations": [""], "is_nested": True}
        expected_dict = {"rib_name_is_none": True}

        rib = RibSchemeImpl.model_validate(input_dict)
        assert (rib.rib_name is None) == expected_dict["rib_name_is_none"]

    def test_validate_inherit_with_reference(self):
        """✅ 校验规则 12：继承来源有 inherit_from"""
        input_dict = {"source_type": "inherit", "inherit_from": "rib1", "operations": ["flip"], "rib_name": "rib5"}
        expected_dict = {"inherit_from": "rib1"}

        rib = RibSchemeImpl.model_validate(input_dict)
        assert rib.inherit_from == expected_dict["inherit_from"]

    def test_validate_inherit_without_reference(self):
        """❌ 校验规则 12：继承来源没有 inherit_from"""
        input_dict = {"source_type": "inherit", "inherit_from": None, "operations": ["flip"], "rib_name": "rib5"}

        with pytest.raises(ValueError, match="继承来源必须指定inherit_from"):
            RibSchemeImpl.model_validate(input_dict)


# ===================== RibSchemeImpl 可变性测试 =====================

class TestRibSchemeImplMutability:
    """RibSchemeImpl 可变性测试（validate_assignment=True）"""

    def test_runtime_fill_fields(self):
        """运行时填充字段"""
        input_dict = {"source_type": "original", "operations": [""], "rib_name": "rib1"}
        expected_dict = {"small_image": "base64_data", "num_pitchs": 10, "rib_height": 100}

        rib = RibSchemeImpl.model_validate(input_dict)
        rib.small_image = expected_dict["small_image"]
        rib.num_pitchs = expected_dict["num_pitchs"]
        rib.rib_height = expected_dict["rib_height"]

        assert rib.small_image == expected_dict["small_image"]
        assert rib.num_pitchs == expected_dict["num_pitchs"]
        assert rib.rib_height == expected_dict["rib_height"]


# ===================== DecorationImpl 校验规则测试 =====================

class TestDecorationImplValidation:
    """DecorationImpl 校验规则测试"""

    def test_decoration_opacity_min(self):
        """✅ 校验规则 13：decoration_opacity = 0"""
        input_dict = {"decoration_opacity": 0, "decoration_width": 100, "decoration_height": 100}
        expected_dict = {"decoration_opacity": 0}

        impl = DecorationImpl.model_validate(input_dict)
        assert impl.decoration_opacity == expected_dict["decoration_opacity"]

    def test_decoration_opacity_max(self):
        """✅ 校验规则 13：decoration_opacity = 255"""
        input_dict = {"decoration_opacity": 255, "decoration_width": 100, "decoration_height": 100}
        expected_dict = {"decoration_opacity": 255}

        impl = DecorationImpl.model_validate(input_dict)
        assert impl.decoration_opacity == expected_dict["decoration_opacity"]

    def test_decoration_opacity_under(self):
        """❌ 校验规则 13：decoration_opacity = -1"""
        input_dict = {"decoration_opacity": -1, "decoration_width": 100, "decoration_height": 100}

        with pytest.raises(ValueError):
            DecorationImpl.model_validate(input_dict)

    def test_decoration_opacity_over(self):
        """❌ 校验规则 13：decoration_opacity = 256"""
        input_dict = {"decoration_opacity": 256, "decoration_width": 100, "decoration_height": 100}

        with pytest.raises(ValueError):
            DecorationImpl.model_validate(input_dict)
