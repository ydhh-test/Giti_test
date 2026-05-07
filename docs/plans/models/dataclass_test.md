# 数据类测试计划

## 1. 测试文件组织

```
tests/
└── unittests/
    └── models/
        ├── test_tire_struct.py        # TireStruct 测试
        ├── test_image_models.py       # 图像模型测试
        ├── test_scheme_models.py      # 方案模型测试
        └── test_rule_models.py        # 规则模型测试
```

不包含：
- 枚举测试 — 枚举值是静态定义，测试无意义
- 集成测试 — 现在只实装数据类，测集成不全面

---

## 2. 测试逻辑

### 2.1 测试的核心目标

**数据类的核心价值 = 约束**

根据 `dataclass_design.md` 第 5 节，数据类定义了 **15 个校验规则**：
- 11 个 model_validator（业务逻辑校验）
- 4 个 Field 约束（数值范围校验）

**测试的核心逻辑 = 验证约束生效**

### 2.2 测试的层次逻辑

```
第一层：校验规则（P0，必须通过）
    ├── model_validator 测试
    └── Field 约束测试

第二层：可变性规则（P0，必须通过）
    ├── validate_assignment=True 的类
    └── frozen=True 的类

第三层：属性与方法（P1，辅助验证）
    ├── name 属性自动提取
    └── 方法正确性
```

---

## 3. 校验规则全覆盖表

| # | 类名 | 校验规则 | 错误信息 | 测试文件 |
|---|------|---------|---------|---------|
| 1 | TireStruct | 必须有小图或大图 | "必须输入小图或大图，流程无法执行" | test_tire_struct.py |
| 2 | TireStruct | scheme_rank >= 1 | "方案排名必须>=1" | test_tire_struct.py |
| 3 | BaseImage | base64格式检查 | "image_base64必须包含data:image/\*;base64,前缀" | test_image_models.py |
| 4 | ImageMeta | width/height >= 1 | Field约束 | test_image_models.py |
| 5 | ImageMeta | channels 1-4 | Field约束 | test_image_models.py |
| 6 | ImageMeta | 尺寸<=10000 | "图像尺寸超过上限10000像素" | test_image_models.py |
| 7 | ImageBiz | 原始数据必须有region | "原始数据必须指定region" | test_image_models.py |
| 8 | ImageBiz | 继承来源必须有inherit_from | "继承来源必须指定inherit_from" | test_image_models.py |
| 9 | ImageEvaluation | 规则名称不能重复 | "规则名称不能重复" | test_image_models.py |
| 10 | RuleEvaluation | feature/score名称一致 | "feature.name != rule name" | test_image_models.py |
| 11 | RibSchemeImpl | 最外层必须有rib_name | "最外层RIB必须有rib_name" | test_scheme_models.py |
| 12 | RibSchemeImpl | 继承来源必须有inherit_from | "继承来源必须指定inherit_from" | test_scheme_models.py |
| 13 | DecorationImpl | decoration_opacity 0~255 | Field约束 | test_scheme_models.py |
| 14 | Rule17Config | edge_continuity 0~1 | Field约束 | test_rule_models.py |
| 15 | Rule8Config | groove_width > 0 | Field约束 | test_rule_models.py |

---

## 4. 测试用例编写规范

### 4.1 Pydantic 序列化/反序列化

```python
# 序列化（对象 → dict）
model.model_dump()
model.model_dump_json()

# 反序列化（dict → 对象）
ModelClass.model_validate(dict_data)
ModelClass.model_validate_json(json_str)
```

### 4.2 测试用例编写模式

**核心要求**：
1. 先定义输入 dict
2. 先定义期望 dict
3. 用输入 dict 填装类（`model_validate`）
4. 验证结果：**右侧必须从 expected_dict 取值**

**错误示例**：
```python
# ❌ 错误：右侧硬编码
assert tire.scheme_rank == 1
assert meta.width == 512
```

**正确示例**：
```python
# ✅ 正确：右侧从 expected_dict 取
input_dict = {"small_images": [...], "rules_config": [], "scheme_rank": 1}
expected_dict = {"scheme_rank": 1}

tire = TireStruct.model_validate(input_dict)
assert tire.scheme_rank == expected_dict["scheme_rank"]
```

### 4.3 深度序列化/反序列化测试

```python
def test_deep_serialization():
    input_dict = {
        "small_images": [{"image_base64": "data:image/png;base64,xxx", "meta": {"width": 512, ...}, "biz": {...}}],
        "rules_config": []
    }
    expected_dict = {"width": 512, "region": "side"}
    
    tire = TireStruct.model_validate(input_dict)
    
    # 验证嵌套对象（右侧从 expected_dict 取）
    assert tire.small_images[0].meta.width == expected_dict["width"]
    assert tire.small_images[0].biz.region.value == expected_dict["region"]
    
    # 验证深度序列化（右侧从 expected_dict 取）
    output_dict = tire.model_dump()
    assert output_dict["small_images"][0]["meta"]["width"] == expected_dict["width"]
```

---

## 5. 测试用例

### 5.1 test_tire_struct.py

```python
import pytest
from src.models.tire_struct import TireStruct

# ===================== 测试数据（模块级常量）=====================

META_DICT = {"width": 512, "height": 512, "channels": 3, "mode": "RGB", "format": "png", "size": 10000}

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
```

---

### 5.2 test_image_models.py

```python
import pytest
from src.models.image_models import SmallImage, ImageMeta, ImageBiz, ImageEvaluation, RuleEvaluation

# ===================== 测试数据（模块级常量）=====================

META_DICT = {"width": 512, "height": 512, "channels": 3, "mode": "RGB", "format": "png", "size": 10000}

BIZ_DICT = {"level": "small", "region": "side", "source_type": "original"}

SMALL_IMAGE_DICT = {"image_base64": "data:image/png;base64,xxx", "meta": META_DICT, "biz": BIZ_DICT}

RULE8_CONFIG_DICT = {"description": "test", "max_score": 4, "activation_node_name": "", "groove_width_center": 10.0, "groove_width_side": 8.0}

RULE11_CONFIG_DICT = {"description": "test", "max_score": 4, "activation_node_name": "", "groove_width": 5.0, "min_width_offset_px": 1, "edge_margin_ratio": 0.1, "min_segment_length_ratio": 0.5, "max_angle_from_vertical": 15.0, "max_count_center": 3, "max_count_side": 2}


# ===================== ImageMeta 校验规则测试 =====================

class TestImageMetaValidation:
    """ImageMeta 校验规则测试"""

    def test_field_constraints_width_valid(self):
        """✅ 校验规则 4：width = 1"""
        input_dict = {**META_DICT, "width": 1}
        expected_dict = {"width": 1}
        
        meta = ImageMeta.model_validate(input_dict)
        assert meta.width == expected_dict["width"]

    def test_field_constraints_width_zero(self):
        """❌ 校验规则 4：width = 0"""
        input_dict = {**META_DICT, "width": 0}
        
        with pytest.raises(ValueError):
            ImageMeta.model_validate(input_dict)

    def test_field_constraints_channels_min(self):
        """✅ 校验规则 5：channels = 1"""
        input_dict = {**META_DICT, "channels": 1, "mode": "GRAY"}
        expected_dict = {"channels": 1}
        
        meta = ImageMeta.model_validate(input_dict)
        assert meta.channels == expected_dict["channels"]

    def test_field_constraints_channels_max(self):
        """✅ 校验规则 5：channels = 4"""
        input_dict = {**META_DICT, "channels": 4, "mode": "RGBA"}
        expected_dict = {"channels": 4}
        
        meta = ImageMeta.model_validate(input_dict)
        assert meta.channels == expected_dict["channels"]

    def test_field_constraints_channels_rgb(self):
        """✅ 校验规则 5：channels = 3 (RGB)"""
        input_dict = {**META_DICT, "channels": 3, "mode": "RGB"}
        expected_dict = {"channels": 3}

        meta = ImageMeta.model_validate(input_dict)
        assert meta.channels == expected_dict["channels"]

    def test_field_constraints_channels_zero(self):
        """❌ 校验规则 5：channels = 0"""
        input_dict = {**META_DICT, "channels": 0}

        with pytest.raises(ValueError):
            ImageMeta.model_validate(input_dict)

    def test_field_constraints_channels_five(self):
        """❌ 校验规则 5：channels = 5 超出范围"""
        input_dict = {**META_DICT, "channels": 5}

        with pytest.raises(ValueError):
            ImageMeta.model_validate(input_dict)

    def test_model_validator_dimensions_at_limit(self):
        """✅ 校验规则 6：width = 10000"""
        input_dict = {**META_DICT, "width": 10000}
        expected_dict = {"width": 10000}
        
        meta = ImageMeta.model_validate(input_dict)
        assert meta.width == expected_dict["width"]

    def test_model_validator_dimensions_over(self):
        """❌ 校验规则 6：width = 10001"""
        input_dict = {**META_DICT, "width": 10001}

        with pytest.raises(ValueError, match="图像尺寸超过上限10000像素"):
            ImageMeta.model_validate(input_dict)


# ===================== ImageBiz 校验规则测试 =====================

class TestImageBizValidation:
    """ImageBiz 校验规则测试"""

    def test_validate_region_for_original_with_region(self):
        """✅ 校验规则 7：原始数据有 region"""
        input_dict = {"level": "small", "region": "side", "source_type": "original"}
        expected_dict = {"region": "side"}
        
        biz = ImageBiz.model_validate(input_dict)
        assert biz.region.value == expected_dict["region"]

    def test_validate_region_for_original_without_region(self):
        """❌ 校验规则 7：原始数据没有 region"""
        input_dict = {"level": "small", "region": None, "source_type": "original"}
        
        with pytest.raises(ValueError, match="原始数据必须指定region"):
            ImageBiz.model_validate(input_dict)

    def test_validate_inherit_with_reference(self):
        """✅ 校验规则 8：继承来源有 inherit_from"""
        input_dict = {"level": "big", "source_type": "inherit", "inherit_from": "rib1"}
        expected_dict = {"inherit_from": "rib1"}
        
        biz = ImageBiz.model_validate(input_dict)
        assert biz.inherit_from == expected_dict["inherit_from"]

    def test_validate_inherit_without_reference(self):
        """❌ 校验规则 8：继承来源没有 inherit_from"""
        input_dict = {"level": "big", "source_type": "inherit", "inherit_from": None}
        
        with pytest.raises(ValueError, match="继承来源必须指定inherit_from"):
            ImageBiz.model_validate(input_dict)


# ===================== BaseImage 校验规则测试 =====================

class TestBaseImageValidation:
    """BaseImage 校验规则测试"""

    def test_validate_base64_format_valid(self):
        """✅ 校验规则 3：包含 data:image/ 前缀"""
        input_dict = SMALL_IMAGE_DICT
        expected_dict = {"has_prefix": True}
        
        image = SmallImage.model_validate(input_dict)
        assert image.image_base64.startswith("data:image/") == expected_dict["has_prefix"]

    def test_validate_base64_format_jpeg(self):
        """✅ 校验规则 3：包含 data:image/jpeg 前缀"""
        input_dict = {**SMALL_IMAGE_DICT, "image_base64": "data:image/jpeg;base64,/9j/4AAQ"}
        expected_dict = {"has_prefix": True}

        image = SmallImage.model_validate(input_dict)
        assert image.image_base64.startswith("data:image/") == expected_dict["has_prefix"]

    def test_validate_base64_format_invalid(self):
        """❌ 校验规则 3：缺少 data:image/ 前缀"""
        input_dict = {**SMALL_IMAGE_DICT, "image_base64": "invalid"}

        with pytest.raises(ValueError, match="image_base64必须包含data:image"):
            SmallImage.model_validate(input_dict)

    def test_validate_base64_format_missing_prefix(self):
        """❌ 校验规则 3：缺少 data:image/ 前缀，但有 base64 内容"""
        input_dict = {**SMALL_IMAGE_DICT, "image_base64": "iVBORw0KGgo="}

        with pytest.raises(ValueError, match="image_base64必须包含data:image"):
            SmallImage.model_validate(input_dict)

    def test_validate_base64_format_wrong_prefix(self):
        """❌ 校验规则 3：错误的前缀格式"""
        input_dict = {**SMALL_IMAGE_DICT, "image_base64": "data:video/mp4;base64,xxx"}

        with pytest.raises(ValueError, match="image_base64必须包含data:image"):
            SmallImage.model_validate(input_dict)


# ===================== ImageEvaluation 校验规则测试 =====================

class TestImageEvaluationValidation:
    """ImageEvaluation 校验规则测试"""

    def test_validate_unique_names_valid(self):
        """✅ 校验规则 9：名称不重复"""
        input_dict = {"rules": [{"name": "rule8", "config": RULE8_CONFIG_DICT}, {"name": "rule11", "config": RULE11_CONFIG_DICT}]}
        expected_dict = {"rules_count": 2}
        
        evaluation = ImageEvaluation.model_validate(input_dict)
        assert len(evaluation.rules) == expected_dict["rules_count"]

    def test_validate_unique_names_duplicate(self):
        """❌ 校验规则 9：名称重复"""
        input_dict = {"rules": [{"name": "rule8", "config": RULE8_CONFIG_DICT}, {"name": "rule8", "config": RULE8_CONFIG_DICT}]}
        
        with pytest.raises(ValueError, match="规则名称不能重复"):
            ImageEvaluation.model_validate(input_dict)


class TestImageEvaluationMethods:
    """ImageEvaluation 方法测试"""

    def test_set_score_updates_total(self):
        """设置评分后自动更新总分"""
        from src.models.rule_models import Rule8Score, Rule11Score
        input_dict = {"rules": [{"name": "rule8", "config": RULE8_CONFIG_DICT}, {"name": "rule11", "config": RULE11_CONFIG_DICT}]}
        expected_dict = {"current_score": 7}
        
        evaluation = ImageEvaluation.model_validate(input_dict)
        evaluation.set_score("rule8", Rule8Score(score=4))
        evaluation.set_score("rule11", Rule11Score(score=3))
        
        assert evaluation.current_score == expected_dict["current_score"]


# ===================== RuleEvaluation 校验规则测试 =====================

class TestRuleEvaluationValidation:
    """RuleEvaluation 校验规则测试"""

    def test_validate_name_consistency_valid(self):
        """✅ 校验规则 10：feature 和 score 名称一致"""
        input_dict = {"name": "rule8", "config": RULE8_CONFIG_DICT, "feature": {"num_transverse_grooves": 5}, "score": {"score": 4}}
        expected_dict = {"name": "rule8"}
        
        evaluation = RuleEvaluation.model_validate(input_dict)
        assert evaluation.name == expected_dict["name"]

    def test_validate_name_consistency_feature_mismatch(self):
        """❌ 校验规则 10：feature 名称不一致"""
        input_dict = {"name": "rule8", "config": RULE8_CONFIG_DICT, "feature": {"num_longitudinal_grooves": 3}}

        with pytest.raises(ValueError, match="feature.name"):
            RuleEvaluation.model_validate(input_dict)

    def test_validate_name_consistency_score_mismatch(self):
        """❌ 校验规则 10：score 名称不一致"""
        input_dict = {"name": "rule8", "config": RULE8_CONFIG_DICT, "score": {"score": 4}}

        with pytest.raises(ValueError, match="score.name"):
            RuleEvaluation.model_validate(input_dict)
```

---

### 5.3 test_scheme_models.py

```python
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
```

---

### 5.4 test_rule_models.py

```python
import pytest
from src.models.rule_models import (
    Rule8Config, Rule8Feature, Rule8Score,
    Rule11Config, Rule11Feature,
    get_feature_class, get_score_class
)

# ===================== 测试数据（模块级常量）=====================

RULE8_CONFIG_DICT = {"description": "横沟数量约束", "max_score": 4, "activation_node_name": "node4", "groove_width_center": 10.0, "groove_width_side": 8.0}

RULE11_CONFIG_DICT = {"description": "test", "max_score": 4, "activation_node_name": "", "groove_width": 5.0, "min_width_offset_px": 1, "edge_margin_ratio": 0.1, "min_segment_length_ratio": 0.5, "max_angle_from_vertical": 15.0, "max_count_center": 3, "max_count_side": 2}

RULE17_CONFIG_DICT = {"description": "", "max_score": 0, "activation_node_name": "", "edge_continuity_rib1_rib2": 0.5, "edge_continuity_rib4_rib5": 0.5, "blend_width": 10}


# ===================== Field 约束测试 =====================

class TestFieldConstraints:
    """Field 约束测试"""

    def test_rule17_edge_continuity_valid(self):
        """✅ 校验规则 14：edge_continuity = 0.5"""
        from src.models.rule_models import Rule17Config
        input_dict = RULE17_CONFIG_DICT
        expected_dict = {"edge_continuity_rib1_rib2": 0.5}
        
        config = Rule17Config.model_validate(input_dict)
        assert config.edge_continuity_rib1_rib2 == expected_dict["edge_continuity_rib1_rib2"]

    def test_rule17_edge_continuity_over(self):
        """❌ 校验规则 14：edge_continuity > 1"""
        from src.models.rule_models import Rule17Config
        input_dict = {**RULE17_CONFIG_DICT, "edge_continuity_rib1_rib2": 1.5}
        
        with pytest.raises(ValueError):
            Rule17Config.model_validate(input_dict)

    def test_rule8_groove_width_valid(self):
        """✅ 校验规则 15：groove_width > 0"""
        input_dict = RULE8_CONFIG_DICT
        expected_dict = {"groove_width_center": 10.0}
        
        config = Rule8Config.model_validate(input_dict)
        assert config.groove_width_center == expected_dict["groove_width_center"]

    def test_rule8_groove_width_zero(self):
        """❌ 校验规则 15：groove_width = 0"""
        input_dict = {**RULE8_CONFIG_DICT, "groove_width_center": 0}
        
        with pytest.raises(ValueError):
            Rule8Config.model_validate(input_dict)


# ===================== name 属性自动提取测试 =====================

class TestRuleNameExtraction:
    """规则 name 属性自动提取测试"""

    def test_config_name_rule8(self):
        """Rule8Config.name == "rule8" """
        input_dict = RULE8_CONFIG_DICT
        expected_dict = {"name": "rule8"}
        
        config = Rule8Config.model_validate(input_dict)
        assert config.name == expected_dict["name"]

    def test_feature_name_rule8(self):
        """Rule8Feature.name == "rule8" """
        input_dict = {"num_transverse_grooves": 5}
        expected_dict = {"name": "rule8"}
        
        feature = Rule8Feature.model_validate(input_dict)
        assert feature.name == expected_dict["name"]

    def test_config_name_rule11(self):
        """Rule11Config.name == "rule11" """
        input_dict = RULE11_CONFIG_DICT
        expected_dict = {"name": "rule11"}
        
        config = Rule11Config.model_validate(input_dict)
        assert config.name == expected_dict["name"]

    def test_no_name_field_in_config(self):
        """Config 类不应手动定义 name 字段"""
        expected_dict = {"has_name_field": False, "name_is_property": True}
        
        assert ('name' in Rule8Config.model_fields) == expected_dict["has_name_field"]
        assert isinstance(Rule8Config.name, property) == expected_dict["name_is_property"]

    def test_no_name_field_in_feature(self):
        """Feature 类不应手动定义 name 字段"""
        expected_dict = {"has_name_field": False, "name_is_property": True}
        
        assert ('name' in Rule8Feature.model_fields) == expected_dict["has_name_field"]
        assert isinstance(Rule8Feature.name, property) == expected_dict["name_is_property"]


# ===================== 注册机制测试 =====================

class TestRuleRegistry:
    """规则注册机制测试"""

    def test_get_feature_class_rule8(self):
        """根据规则名获取 Rule8Feature"""
        expected_dict = {"class": Rule8Feature}
        feature_cls = get_feature_class("rule8")
        assert feature_cls == expected_dict["class"]

    def test_get_feature_class_not_found(self):
        """获取不存在的 Feature 类"""
        expected_dict = {"result": None}
        feature_cls = get_feature_class("rule999")
        assert feature_cls == expected_dict["result"]

    def test_get_score_class_rule8(self):
        """根据规则名获取 Rule8Score"""
        expected_dict = {"class": Rule8Score}
        score_cls = get_score_class("rule8")
        assert score_cls == expected_dict["class"]

    def test_dynamic_instantiation(self):
        """动态获取类并实例化"""
        feature_cls = get_feature_class("rule8")
        input_dict = {"num_transverse_grooves": 5}
        expected_dict = {"num_transverse_grooves": 5}
        
        feature = feature_cls.model_validate(input_dict)
        assert feature.num_transverse_grooves == expected_dict["num_transverse_grooves"]
```

---

## 6. 测试用例统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 校验规则测试 | 23 | 对应 15 个校验规则，含边界值和格式变体 |
| 可变性测试 | 4 | TireStruct、RibSchemeImpl、模板类 frozen（2个） |
| name 提取测试 | 5 | Config/Feature 的 name 提取 + 无 name 字段验证 |
| 注册机制测试 | 4 | get_feature_class / get_score_class / 动态实例化 |
| 方法测试 | 1 | ImageEvaluation.set_score 自动更新总分 |
| 深度序列化测试 | 6 | 1 正向 + 5 反向嵌套校验 |
| **总计** | **~43** | |

---

## 7. 执行命令

```bash
# 执行所有数据类测试
pytest tests/unittests/models/ -v

# 执行单个测试文件
pytest tests/unittests/models/test_tire_struct.py -v

# 执行单个测试类
pytest tests/unittests/models/test_tire_struct.py::TestTireStructValidation -v

# 生成覆盖率报告
pytest tests/unittests/models/ --cov=src/models --cov-report=term-missing
```

---

**文档结束**
