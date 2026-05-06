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

如果约束不生效，数据类就失去了存在的意义。比如：
- TireStruct 允许 `small_images=[]` 且 `big_image=None` → 流程无法执行
- ImageMeta 允许 `width=0` → 后续计算除零错误
- RibSchemeImpl 允许 `source_type=INHERIT` 但 `inherit_from=None` → 运行时找不到源数据

### 2.2 测试的层次逻辑

```
第一层：校验规则（P0，必须通过）
    │
    ├── model_validator 测试
    │   - 正常场景：验证合法值通过
    │   - 异常场景：验证非法值抛出正确错误信息
    │   - 目的：确保 15 个校验规则全部生效
    │
    └── Field 约束测试
        - 边界值测试：最小值、最大值
        - 非法值测试：负数、超范围
        - 目的：确保数值范围约束生效

第二层：可变性规则（P0，必须通过）
    │
    ├── validate_assignment=True 的类
    │   - 测试运行时修改成功
    │   - 测试非法修改触发校验
    │   - 目的：确保 TireStruct、ImageEvaluation 等可以在 Pipeline 中动态填充
    │
    └── frozen=True 的类
        - 测试修改抛出异常
        - 目的：确保模板类不被误修改

第三层：属性与方法（P1，辅助验证）
    │
    ├── name 属性自动提取
    │   - 验证 Rule8Config().name == "rule8"
    │   - 目的：确保注册机制正常工作
    │
    └── 方法正确性
        - ImageEvaluation.get_rule / set_feature / set_score
        - 目的：确保方法逻辑正确
```

### 2.3 测试设计思路

#### 思路 1：每个校验规则对应一个测试用例

校验规则是数据类的核心价值，每个校验规则都有明确的触发条件和错误信息。

```python
# TireStruct 校验规则 1：必须有小图或大图

def test_validate_images_required_with_small():
    """✅ 正常：有小图"""
    tire_struct = TireStruct(small_images=[create_small_image()])
    assert len(tire_struct.small_images) > 0

def test_validate_images_required_error():
    """❌ 异常：小图和大图都为空"""
    with pytest.raises(ValueError, match="必须输入小图或大图，流程无法执行"):
        TireStruct(small_images=[], big_image=None)
```

好处：
- 测试用例名称直接对应校验规则
- 测试失败时，一眼就知道哪个校验规则有问题

#### 思路 2：可变性规则单独测试

`validate_assignment` 是 Pydantic 的关键特性，设计文档明确要求某些类开启、某些类关闭，关系到运行时数据填充是否正常工作。

```python
class TestTireStructMutability:
    """测试 TireStruct 可变性（validate_assignment=True）"""

    def test_runtime_modification_success():
        tire_struct = TireStruct(small_images=[...])
        tire_struct.flag = True
        assert tire_struct.flag == True

    def test_runtime_modification_validation():
        tire_struct = TireStruct(small_images=[...], scheme_rank=1)
        with pytest.raises(ValueError):
            tire_struct.scheme_rank = 0  # scheme_rank 必须 >= 1

class TestTemplateFrozen:
    """测试模板类不可变"""

    def test_symmetry0_frozen():
        template = Symmetry0()
        with pytest.raises(Exception):
            template.rib_number = 10
```

#### 思路 3：name 属性自动提取单独验证

设计文档明确禁止手动定义 name 字段，name 属性是注册机制的基础，如果 name 提取失败，`get_feature_class("rule8")` 会返回 None。

```python
class TestRuleNameExtraction:

    def test_config_name():
        config = Rule8Config(...)
        assert config.name == "rule8"

    def test_no_name_field():
        # name 不应该是 Field，应该是 property
        assert 'name' not in Rule8Config.model_fields
        assert isinstance(Rule8Config.name, property)
```

#### 思路 4：方法正确性测试

ImageEvaluation 提供了方法（get_rule / set_feature / set_score），这些方法有业务逻辑（自动计算总分、检查名称一致性），需要验证方法逻辑正确。

```python
class TestImageEvaluationMethods:

    def test_set_score_updates_total():
        evaluation = ImageEvaluation(rules=[
            RuleEvaluation(name="rule8", config=...),
            RuleEvaluation(name="rule11", config=...)
        ])
        evaluation.set_score("rule8", Rule8Score(score=4))
        evaluation.set_score("rule11", Rule11Score(score=3))
        assert evaluation.current_score == 7
```

---

## 3. 校验规则全覆盖表

根据 `dataclass_design.md` 第 5 节，15 个校验规则必须全部覆盖：

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

## 4. 测试用例

### 4.1 test_tire_struct.py

```python
import pytest
from src.models.tire_struct import TireStruct
from src.models.image_models import SmallImage, BigImage, ImageMeta, ImageBiz
from src.models.enums import (
    LevelEnum, RegionEnum, SourceTypeEnum,
    ImageModeEnum, ImageFormatEnum
)


# ===================== 测试辅助函数 =====================

def _create_valid_meta(**overrides):
    """创建合法的 ImageMeta"""
    defaults = dict(
        width=512, height=512, channels=3,
        mode=ImageModeEnum.RGB, format=ImageFormatEnum.PNG, size=10000
    )
    defaults.update(overrides)
    return ImageMeta(**defaults)


def _create_valid_biz(**overrides):
    """创建合法的 ImageBiz"""
    defaults = dict(
        level=LevelEnum.SMALL, region=RegionEnum.SIDE,
        source_type=SourceTypeEnum.ORIGINAL
    )
    defaults.update(overrides)
    return ImageBiz(**defaults)


def _create_valid_small_image(**biz_overrides):
    """创建合法的 SmallImage"""
    return SmallImage(
        image_base64="data:image/png;base64,iVBORw0KGgo=",
        meta=_create_valid_meta(),
        biz=_create_valid_biz(**biz_overrides)
    )


def _create_valid_big_image():
    """创建合法的 BigImage"""
    return BigImage(
        image_base64="data:image/png;base64,iVBORw0KGgo=",
        meta=_create_valid_meta(width=1024),
        biz=_create_valid_biz(level=LevelEnum.BIG, source_type=SourceTypeEnum.CONCAT)
    )


# ===================== 校验规则测试 =====================

class TestTireStructValidation:
    """TireStruct 校验规则测试"""

    # 校验规则 1：必须有小图或大图
    def test_validate_images_required_with_small(self):
        """✅ 正常：有小图"""
        tire = TireStruct(small_images=[_create_valid_small_image()])
        assert len(tire.small_images) > 0

    def test_validate_images_required_with_big(self):
        """✅ 正常：有大图"""
        tire = TireStruct(big_image=_create_valid_big_image())
        assert tire.big_image is not None

    def test_validate_images_required_with_both(self):
        """✅ 正常：小图和大图都有"""
        tire = TireStruct(
            small_images=[_create_valid_small_image()],
            big_image=_create_valid_big_image()
        )
        assert len(tire.small_images) > 0
        assert tire.big_image is not None

    def test_validate_images_required_error(self):
        """❌ 异常：小图和大图都为空"""
        with pytest.raises(ValueError, match="必须输入小图或大图，流程无法执行"):
            TireStruct(small_images=[], big_image=None)

    # 校验规则 2：scheme_rank >= 1
    def test_validate_scheme_rank_valid(self):
        """✅ 正常：scheme_rank = 1"""
        tire = TireStruct(
            small_images=[_create_valid_small_image()],
            scheme_rank=1
        )
        assert tire.scheme_rank == 1

    def test_validate_scheme_rank_large(self):
        """✅ 正常：scheme_rank = 10"""
        tire = TireStruct(
            small_images=[_create_valid_small_image()],
            scheme_rank=10
        )
        assert tire.scheme_rank == 10

    def test_validate_scheme_rank_none(self):
        """✅ 正常：scheme_rank 为 None（可选字段）"""
        tire = TireStruct(
            small_images=[_create_valid_small_image()]
        )
        assert tire.scheme_rank is None

    def test_validate_scheme_rank_error_zero(self):
        """❌ 异常：scheme_rank = 0"""
        with pytest.raises(ValueError, match="方案排名必须>=1"):
            TireStruct(
                small_images=[_create_valid_small_image()],
                scheme_rank=0
            )

    def test_validate_scheme_rank_error_negative(self):
        """❌ 异常：scheme_rank = -1"""
        with pytest.raises(ValueError, match="方案排名必须>=1"):
            TireStruct(
                small_images=[_create_valid_small_image()],
                scheme_rank=-1
            )


# ===================== 可变性测试 =====================

class TestTireStructMutability:
    """TireStruct 可变性测试（validate_assignment=True）"""

    def test_runtime_modification_flag(self):
        """运行时修改 flag"""
        tire = TireStruct(small_images=[_create_valid_small_image()])
        tire.flag = True
        assert tire.flag == True

        tire.flag = False
        assert tire.flag == False

    def test_runtime_modification_err_msg(self):
        """运行时修改 err_msg"""
        tire = TireStruct(small_images=[_create_valid_small_image()])
        tire.err_msg = "执行失败"
        assert tire.err_msg == "执行失败"

    def test_runtime_modification_scheme_rank(self):
        """运行时修改 scheme_rank"""
        tire = TireStruct(
            small_images=[_create_valid_small_image()],
            scheme_rank=1
        )
        tire.scheme_rank = 5
        assert tire.scheme_rank == 5

    def test_runtime_validation_scheme_rank(self):
        """运行时修改 scheme_rank 为非法值触发校验"""
        tire = TireStruct(
            small_images=[_create_valid_small_image()],
            scheme_rank=1
        )
        with pytest.raises(ValueError):
            tire.scheme_rank = 0
```

---

### 4.2 test_image_models.py

```python
import pytest
from src.models.image_models import (
    SmallImage, BigImage, ImageMeta, ImageBiz,
    ImageEvaluation, RuleEvaluation, ImageScore, ImageLineage
)
from src.models.enums import (
    LevelEnum, RegionEnum, SourceTypeEnum,
    ImageModeEnum, ImageFormatEnum
)
from src.models.rule_models import (
    Rule8Config, Rule8Feature, Rule8Score,
    Rule11Config, Rule11Feature, Rule11Score
)


# ===================== 测试辅助函数 =====================

def _create_valid_meta(**overrides):
    defaults = dict(
        width=512, height=512, channels=3,
        mode=ImageModeEnum.RGB, format=ImageFormatEnum.PNG, size=10000
    )
    defaults.update(overrides)
    return ImageMeta(**defaults)


def _create_valid_biz(**overrides):
    defaults = dict(
        level=LevelEnum.SMALL, region=RegionEnum.SIDE,
        source_type=SourceTypeEnum.ORIGINAL
    )
    defaults.update(overrides)
    return ImageBiz(**defaults)


def _create_rule8_config():
    return Rule8Config(
        description="横沟数量约束",
        max_score=4,
        activation_node_name="node4",
        groove_width_center=10.0,
        groove_width_side=8.0
    )


def _create_rule11_config():
    return Rule11Config(
        description="纵向钢片与纵向细沟数量约束",
        max_score=4,
        activation_node_name="node4",
        groove_width=5.0,
        min_width_offset_px=1,
        edge_margin_ratio=0.1,
        min_segment_length_ratio=0.5,
        max_angle_from_vertical=15.0,
        max_count_center=3,
        max_count_side=2
    )


# ===================== ImageMeta 校验规则测试 =====================

class TestImageMetaValidation:
    """ImageMeta 校验规则测试"""

    # 校验规则 4：width/height >= 1（Field 约束）
    def test_field_constraints_width_valid(self):
        """✅ 正常：width = 1"""
        meta = _create_valid_meta(width=1)
        assert meta.width == 1

    def test_field_constraints_width_zero(self):
        """❌ 异常：width = 0"""
        with pytest.raises(ValueError):
            _create_valid_meta(width=0)

    def test_field_constraints_width_negative(self):
        """❌ 异常：width = -1"""
        with pytest.raises(ValueError):
            _create_valid_meta(width=-1)

    def test_field_constraints_height_valid(self):
        """✅ 正常：height = 1"""
        meta = _create_valid_meta(height=1)
        assert meta.height == 1

    def test_field_constraints_height_zero(self):
        """❌ 异常：height = 0"""
        with pytest.raises(ValueError):
            _create_valid_meta(height=0)

    # 校验规则 5：channels 1-4（Field 约束）
    def test_field_constraints_channels_min(self):
        """✅ 正常：channels = 1"""
        meta = _create_valid_meta(channels=1, mode=ImageModeEnum.GRAY)
        assert meta.channels == 1

    def test_field_constraints_channels_max(self):
        """✅ 正常：channels = 4"""
        meta = _create_valid_meta(channels=4, mode=ImageModeEnum.RGBA)
        assert meta.channels == 4

    def test_field_constraints_channels_zero(self):
        """❌ 异常：channels = 0"""
        with pytest.raises(ValueError):
            _create_valid_meta(channels=0)

    def test_field_constraints_channels_over(self):
        """❌ 异常：channels = 5"""
        with pytest.raises(ValueError):
            _create_valid_meta(channels=5)

    # 校验规则 6：尺寸 <= 10000（model_validator）
    def test_model_validator_dimensions_at_limit(self):
        """✅ 正常：width = 10000"""
        meta = _create_valid_meta(width=10000)
        assert meta.width == 10000

    def test_model_validator_dimensions_height_at_limit(self):
        """✅ 正常：height = 10000"""
        meta = _create_valid_meta(height=10000)
        assert meta.height == 10000

    def test_model_validator_dimensions_width_over(self):
        """❌ 异常：width = 10001"""
        with pytest.raises(ValueError, match="图像尺寸超过上限10000像素"):
            _create_valid_meta(width=10001)

    def test_model_validator_dimensions_height_over(self):
        """❌ 异常：height = 10001"""
        with pytest.raises(ValueError, match="图像尺寸超过上限10000像素"):
            _create_valid_meta(height=10001)


# ===================== ImageBiz 校验规则测试 =====================

class TestImageBizValidation:
    """ImageBiz 校验规则测试"""

    # 校验规则 7：原始数据必须有 region
    def test_validate_region_for_original_with_region(self):
        """✅ 正常：原始数据有 region"""
        biz = _create_valid_biz(
            level=LevelEnum.SMALL,
            region=RegionEnum.SIDE,
            source_type=SourceTypeEnum.ORIGINAL
        )
        assert biz.region == RegionEnum.SIDE

    def test_validate_region_for_original_without_region(self):
        """❌ 异常：原始数据没有 region"""
        with pytest.raises(ValueError, match="原始数据必须指定region"):
            ImageBiz(
                level=LevelEnum.SMALL,
                region=None,
                source_type=SourceTypeEnum.ORIGINAL
            )

    # 校验规则 8：继承来源必须有 inherit_from
    def test_validate_inherit_with_reference(self):
        """✅ 正常：继承来源有 inherit_from"""
        biz = ImageBiz(
            level=LevelEnum.BIG,
            source_type=SourceTypeEnum.INHERIT,
            inherit_from="rib1"
        )
        assert biz.inherit_from == "rib1"

    def test_validate_inherit_without_reference(self):
        """❌ 异常：继承来源没有 inherit_from"""
        with pytest.raises(ValueError, match="继承来源必须指定inherit_from"):
            ImageBiz(
                level=LevelEnum.BIG,
                source_type=SourceTypeEnum.INHERIT,
                inherit_from=None
            )


# ===================== BaseImage 校验规则测试 =====================

class TestBaseImageValidation:
    """BaseImage 校验规则测试"""

    # 校验规则 3：base64 格式检查
    def test_validate_base64_format_valid(self):
        """✅ 正常：包含 data:image/ 前缀"""
        image = SmallImage(
            image_base64="data:image/png;base64,iVBORw0KGgo=",
            meta=_create_valid_meta(),
            biz=_create_valid_biz()
        )
        assert image.image_base64.startswith("data:image/")

    def test_validate_base64_format_invalid(self):
        """❌ 异常：缺少 data:image/ 前缀"""
        with pytest.raises(ValueError, match="image_base64必须包含data:image"):
            SmallImage(
                image_base64="iVBORw0KGgo=",
                meta=_create_valid_meta(),
                biz=_create_valid_biz()
            )

    def test_validate_base64_format_empty(self):
        """❌ 异常：空字符串"""
        with pytest.raises(ValueError, match="image_base64必须包含data:image"):
            SmallImage(
                image_base64="",
                meta=_create_valid_meta(),
                biz=_create_valid_biz()
            )


# ===================== ImageEvaluation 校验规则测试 =====================

class TestImageEvaluationValidation:
    """ImageEvaluation 校验规则测试"""

    # 校验规则 9：规则名称不能重复
    def test_validate_unique_names_valid(self):
        """✅ 正常：名称不重复"""
        evaluation = ImageEvaluation(rules=[
            RuleEvaluation(name="rule8", config=_create_rule8_config()),
            RuleEvaluation(name="rule11", config=_create_rule11_config())
        ])
        assert len(evaluation.rules) == 2

    def test_validate_unique_names_duplicate(self):
        """❌ 异常：名称重复"""
        with pytest.raises(ValueError, match="规则名称不能重复"):
            ImageEvaluation(rules=[
                RuleEvaluation(name="rule8", config=_create_rule8_config()),
                RuleEvaluation(name="rule8", config=_create_rule8_config())
            ])


class TestImageEvaluationMethods:
    """ImageEvaluation 方法测试"""

    def test_get_rule_found(self):
        """获取存在的规则"""
        evaluation = ImageEvaluation(rules=[
            RuleEvaluation(name="rule8", config=_create_rule8_config())
        ])
        rule = evaluation.get_rule("rule8")
        assert rule is not None
        assert rule.name == "rule8"

    def test_get_rule_not_found(self):
        """获取不存在的规则"""
        evaluation = ImageEvaluation(rules=[
            RuleEvaluation(name="rule8", config=_create_rule8_config())
        ])
        rule = evaluation.get_rule("rule999")
        assert rule is None

    def test_set_feature(self):
        """设置规则特征"""
        evaluation = ImageEvaluation(rules=[
            RuleEvaluation(name="rule8", config=_create_rule8_config())
        ])
        feature = Rule8Feature(num_transverse_grooves=5)
        evaluation.set_feature("rule8", feature)
        assert evaluation.get_rule("rule8").feature == feature

    def test_set_feature_rule_not_found(self):
        """设置不存在的规则特征"""
        evaluation = ImageEvaluation(rules=[
            RuleEvaluation(name="rule8", config=_create_rule8_config())
        ])
        with pytest.raises(ValueError, match="规则 rule999 不存在"):
            evaluation.set_feature("rule999", Rule8Feature(num_transverse_grooves=5))

    def test_set_score(self):
        """设置规则评分"""
        evaluation = ImageEvaluation(rules=[
            RuleEvaluation(name="rule8", config=_create_rule8_config())
        ])
        evaluation.set_score("rule8", Rule8Score(score=4))
        assert evaluation.get_rule("rule8").score.score == 4

    def test_set_score_updates_total(self):
        """设置评分后自动更新总分"""
        evaluation = ImageEvaluation(rules=[
            RuleEvaluation(name="rule8", config=_create_rule8_config()),
            RuleEvaluation(name="rule11", config=_create_rule11_config())
        ])
        evaluation.set_score("rule8", Rule8Score(score=4))
        evaluation.set_score("rule11", Rule11Score(score=3))
        assert evaluation.current_score == 7


# ===================== RuleEvaluation 校验规则测试 =====================

class TestRuleEvaluationValidation:
    """RuleEvaluation 校验规则测试"""

    # 校验规则 10：feature/score 名称一致
    def test_validate_name_consistency_valid(self):
        """✅ 正常：feature 和 score 名称一致"""
        evaluation = RuleEvaluation(
            name="rule8",
            config=_create_rule8_config(),
            feature=Rule8Feature(num_transverse_grooves=5),
            score=Rule8Score(score=4)
        )
        assert evaluation.name == "rule8"

    def test_validate_name_consistency_feature_mismatch(self):
        """❌ 异常：feature 名称不一致"""
        with pytest.raises(ValueError, match="feature.name"):
            RuleEvaluation(
                name="rule8",
                config=_create_rule8_config(),
                feature=Rule11Feature(num_longitudinal_grooves=3)
            )

    def test_validate_name_consistency_score_mismatch(self):
        """❌ 异常：score 名称不一致"""
        with pytest.raises(ValueError, match="score.name"):
            RuleEvaluation(
                name="rule8",
                config=_create_rule8_config(),
                score=Rule11Score(score=4)
            )


# ===================== RuleEvaluation 可变性测试 =====================

class TestRuleEvaluationMutability:
    """RuleEvaluation 可变性测试（validate_assignment=True）"""

    def test_runtime_fill_feature(self):
        """运行时填充 feature"""
        evaluation = RuleEvaluation(
            name="rule8",
            config=_create_rule8_config()
        )
        evaluation.feature = Rule8Feature(num_transverse_grooves=5)
        assert evaluation.feature is not None

    def test_runtime_fill_score(self):
        """运行时填充 score"""
        evaluation = RuleEvaluation(
            name="rule8",
            config=_create_rule8_config()
        )
        evaluation.score = Rule8Score(score=4)
        assert evaluation.score is not None

    def test_runtime_fill_feature_name_mismatch(self):
        """运行时填充不一致的 feature 触发校验"""
        evaluation = RuleEvaluation(
            name="rule8",
            config=_create_rule8_config()
        )
        with pytest.raises(ValueError):
            evaluation.feature = Rule11Feature(num_longitudinal_grooves=3)


# ===================== ImageEvaluation 可变性测试 =====================

class TestImageEvaluationMutability:
    """ImageEvaluation 可变性测试（validate_assignment=True）"""

    def test_runtime_modify_current_score(self):
        """运行时修改 current_score"""
        evaluation = ImageEvaluation(rules=[
            RuleEvaluation(name="rule8", config=_create_rule8_config())
        ])
        evaluation.current_score = 10
        assert evaluation.current_score == 10

    def test_runtime_modify_current_score_invalid(self):
        """运行时修改 current_score 为非法值触发校验"""
        evaluation = ImageEvaluation(rules=[
            RuleEvaluation(name="rule8", config=_create_rule8_config())
        ])
        with pytest.raises(ValueError):
            evaluation.current_score = -1
```

---

### 4.3 test_scheme_models.py

```python
import pytest
from src.models.scheme_models import (
    RibTemplate, StitchingTemplate,
    Symmetry0, Symmetry1, Continuity0, _Concatenate0,
    RibSchemeImpl, StitchingScheme, StitchingSchemeAbstract,
    MainGrooveImpl, MainGrooveScheme, MainGrooveSchemeAbstract,
    DecorationImpl, DecorationScheme, DecorationSchemeAbstract
)
from src.models.enums import (
    RegionEnum, SourceTypeEnum, StitchingSchemeName, RibOperation
)


# ===================== 模板类 frozen 测试 =====================

class TestTemplateFrozen:
    """模板类 frozen 测试"""

    def test_rib_template_frozen(self):
        """RibTemplate 不可修改"""
        rib = RibTemplate(
            region=RegionEnum.SIDE,
            operation_template=(RibOperation.NONE,),
            rib_name="rib1"
        )
        with pytest.raises(Exception):
            rib.region = RegionEnum.CENTER

    def test_stitching_template_frozen(self):
        """StitchingTemplate 子类不可修改"""
        template = Symmetry0()
        with pytest.raises(Exception):
            template.rib_number = 10

    def test_symmetry1_frozen(self):
        """Symmetry1 不可修改"""
        template = Symmetry1()
        with pytest.raises(Exception):
            template.name = StitchingSchemeName.SYMMETRY_0

    def test_continuity0_frozen(self):
        """Continuity0 不可修改"""
        template = Continuity0()
        with pytest.raises(Exception):
            template.mode = "other"


# ===================== RibSchemeImpl 校验规则测试 =====================

class TestRibSchemeImplValidation:
    """RibSchemeImpl 校验规则测试"""

    # 校验规则 11：最外层必须有 rib_name
    def test_validate_name_required_top_level_with_name(self):
        """✅ 正常：最外层有 rib_name"""
        rib = RibSchemeImpl(
            source_type=SourceTypeEnum.ORIGINAL,
            operations=(RibOperation.NONE,),
            rib_name="rib1",
            is_nested=False
        )
        assert rib.rib_name == "rib1"

    def test_validate_name_required_top_level_without_name(self):
        """❌ 异常：最外层没有 rib_name"""
        with pytest.raises(ValueError, match="最外层RIB必须有rib_name"):
            RibSchemeImpl(
                source_type=SourceTypeEnum.ORIGINAL,
                operations=(RibOperation.NONE,),
                is_nested=False
            )

    def test_validate_name_nested_without_name(self):
        """✅ 正常：嵌套 RIB 可以没有 rib_name"""
        rib = RibSchemeImpl(
            source_type=SourceTypeEnum.ORIGINAL,
            operations=(RibOperation.NONE,),
            is_nested=True
        )
        assert rib.rib_name is None

    # 校验规则 12：继承来源必须有 inherit_from
    def test_validate_inherit_with_reference(self):
        """✅ 正常：继承来源有 inherit_from"""
        rib = RibSchemeImpl(
            source_type=SourceTypeEnum.INHERIT,
            inherit_from="rib1",
            operations=(RibOperation.FLIP,),
            rib_name="rib5"
        )
        assert rib.inherit_from == "rib1"

    def test_validate_inherit_without_reference(self):
        """❌ 异常：继承来源没有 inherit_from"""
        with pytest.raises(ValueError, match="继承来源必须指定inherit_from"):
            RibSchemeImpl(
                source_type=SourceTypeEnum.INHERIT,
                inherit_from=None,
                operations=(RibOperation.FLIP,),
                rib_name="rib5"
            )


# ===================== RibSchemeImpl 可变性测试 =====================

class TestRibSchemeImplMutability:
    """RibSchemeImpl 可变性测试（validate_assignment=True）"""

    def test_runtime_fill_small_image(self):
        """运行时填充 small_image"""
        rib = RibSchemeImpl(
            source_type=SourceTypeEnum.ORIGINAL,
            operations=(RibOperation.NONE,),
            rib_name="rib1"
        )
        rib.small_image = "base64_data"
        assert rib.small_image == "base64_data"

    def test_runtime_fill_rib_image(self):
        """运行时填充 rib_image"""
        rib = RibSchemeImpl(
            source_type=SourceTypeEnum.ORIGINAL,
            operations=(RibOperation.NONE,),
            rib_name="rib1"
        )
        rib.rib_image = "processed_base64"
        assert rib.rib_image == "processed_base64"

    def test_runtime_fill_dimensions(self):
        """运行时填充尺寸信息"""
        rib = RibSchemeImpl(
            source_type=SourceTypeEnum.ORIGINAL,
            operations=(RibOperation.NONE,),
            rib_name="rib1"
        )
        rib.num_pitchs = 10
        rib.rib_height = 100
        rib.rib_width = 200
        assert rib.num_pitchs == 10
        assert rib.rib_height == 100
        assert rib.rib_width == 200


# ===================== DecorationImpl 校验规则测试 =====================

class TestDecorationImplValidation:
    """DecorationImpl 校验规则测试"""

    # 校验规则 13：decoration_opacity 0~255
    def test_decoration_opacity_min(self):
        """✅ 正常：decoration_opacity = 0"""
        impl = DecorationImpl(
            decoration_opacity=0,
            decoration_width=100,
            decoration_height=100
        )
        assert impl.decoration_opacity == 0

    def test_decoration_opacity_max(self):
        """✅ 正常：decoration_opacity = 255"""
        impl = DecorationImpl(
            decoration_opacity=255,
            decoration_width=100,
            decoration_height=100
        )
        assert impl.decoration_opacity == 255

    def test_decoration_opacity_under(self):
        """❌ 异常：decoration_opacity = -1"""
        with pytest.raises(ValueError):
            DecorationImpl(
                decoration_opacity=-1,
                decoration_width=100,
                decoration_height=100
            )

    def test_decoration_opacity_over(self):
        """❌ 异常：decoration_opacity = 256"""
        with pytest.raises(ValueError):
            DecorationImpl(
                decoration_opacity=256,
                decoration_width=100,
                decoration_height=100
            )
```

---

### 4.4 test_rule_models.py

```python
import pytest
from src.models.rule_models import (
    BaseRuleConfig, BaseRuleFeature, BaseRuleScore,
    Rule8Config, Rule8Feature, Rule8Score,
    Rule11Config, Rule11Feature, Rule11Score,
    Rule13Config, Rule13Feature, Rule13Score,
    Rule17Config, Rule17Feature, Rule17Score,
    get_feature_class, get_score_class
)


# ===================== Field 约束测试 =====================

class TestFieldConstraints:
    """Field 约束测试"""

    # 校验规则 14：Rule17Config.edge_continuity 0~1
    def test_rule17_edge_continuity_valid(self):
        """✅ 正常：edge_continuity = 0.5"""
        config = Rule17Config(
            description="RIB1与RIB2、RIB4与RIB5可连续可不连续",
            max_score=0,
            activation_node_name="",
            edge_continuity_rib1_rib2=0.5,
            edge_continuity_rib4_rib5=0.5,
            blend_width=10
        )
        assert config.edge_continuity_rib1_rib2 == 0.5

    def test_rule17_edge_continuity_zero(self):
        """✅ 正常：edge_continuity = 0"""
        config = Rule17Config(
            description="",
            max_score=0,
            activation_node_name="",
            edge_continuity_rib1_rib2=0.0,
            edge_continuity_rib4_rib5=0.0,
            blend_width=10
        )
        assert config.edge_continuity_rib1_rib2 == 0.0

    def test_rule17_edge_continuity_one(self):
        """✅ 正常：edge_continuity = 1"""
        config = Rule17Config(
            description="",
            max_score=0,
            activation_node_name="",
            edge_continuity_rib1_rib2=1.0,
            edge_continuity_rib4_rib5=1.0,
            blend_width=10
        )
        assert config.edge_continuity_rib1_rib2 == 1.0

    def test_rule17_edge_continuity_over(self):
        """❌ 异常：edge_continuity > 1"""
        with pytest.raises(ValueError):
            Rule17Config(
                description="",
                max_score=0,
                activation_node_name="",
                edge_continuity_rib1_rib2=1.5,
                edge_continuity_rib4_rib5=0.5,
                blend_width=10
            )

    def test_rule17_edge_continuity_negative(self):
        """❌ 异常：edge_continuity < 0"""
        with pytest.raises(ValueError):
            Rule17Config(
                description="",
                max_score=0,
                activation_node_name="",
                edge_continuity_rib1_rib2=0.5,
                edge_continuity_rib4_rib5=-0.1,
                blend_width=10
            )

    # 校验规则 15：Rule8Config.groove_width > 0
    def test_rule8_groove_width_valid(self):
        """✅ 正常：groove_width > 0"""
        config = Rule8Config(
            description="横沟数量约束",
            max_score=4,
            activation_node_name="node4",
            groove_width_center=10.0,
            groove_width_side=8.0
        )
        assert config.groove_width_center == 10.0

    def test_rule8_groove_width_zero(self):
        """❌ 异常：groove_width = 0"""
        with pytest.raises(ValueError):
            Rule8Config(
                description="",
                max_score=4,
                activation_node_name="",
                groove_width_center=0,
                groove_width_side=8.0
            )

    def test_rule8_groove_width_negative(self):
        """❌ 异常：groove_width < 0"""
        with pytest.raises(ValueError):
            Rule8Config(
                description="",
                max_score=4,
                activation_node_name="",
                groove_width_center=10.0,
                groove_width_side=-1
            )


# ===================== name 属性自动提取测试 =====================

class TestRuleNameExtraction:
    """规则 name 属性自动提取测试"""

    def test_config_name_rule8(self):
        """Rule8Config.name == "rule8" """
        config = Rule8Config(
            description="横沟数量约束",
            max_score=4,
            activation_node_name="node4",
            groove_width_center=10.0,
            groove_width_side=8.0
        )
        assert config.name == "rule8"

    def test_feature_name_rule8(self):
        """Rule8Feature.name == "rule8" """
        feature = Rule8Feature(num_transverse_grooves=5)
        assert feature.name == "rule8"

    def test_score_name_rule8(self):
        """Rule8Score.name == "rule8" """
        score = Rule8Score(score=4)
        assert score.name == "rule8"

    def test_config_name_rule11(self):
        """Rule11Config.name == "rule11" """
        config = Rule11Config(
            description="纵向钢片与纵向细沟数量约束",
            max_score=4,
            activation_node_name="node4",
            groove_width=5.0,
            min_width_offset_px=1,
            edge_margin_ratio=0.1,
            min_segment_length_ratio=0.5,
            max_angle_from_vertical=15.0,
            max_count_center=3,
            max_count_side=2
        )
        assert config.name == "rule11"

    def test_feature_name_rule11(self):
        """Rule11Feature.name == "rule11" """
        feature = Rule11Feature(num_longitudinal_grooves=3)
        assert feature.name == "rule11"

    def test_score_name_rule11(self):
        """Rule11Score.name == "rule11" """
        score = Rule11Score(score=3)
        assert score.name == "rule11"

    def test_no_name_field_in_config(self):
        """Config 类不应手动定义 name 字段"""
        assert 'name' not in Rule8Config.model_fields
        assert isinstance(Rule8Config.name, property)

    def test_no_name_field_in_feature(self):
        """Feature 类不应手动定义 name 字段"""
        assert 'name' not in Rule8Feature.model_fields
        assert isinstance(Rule8Feature.name, property)

    def test_no_name_field_in_score(self):
        """Score 类不应手动定义 name 字段"""
        assert 'name' not in Rule8Score.model_fields
        assert isinstance(Rule8Score.name, property)


# ===================== 注册机制测试 =====================

class TestRuleRegistry:
    """规则注册机制测试"""

    def test_get_feature_class_rule8(self):
        """根据规则名获取 Rule8Feature"""
        feature_cls = get_feature_class("rule8")
        assert feature_cls == Rule8Feature

    def test_get_feature_class_rule11(self):
        """根据规则名获取 Rule11Feature"""
        feature_cls = get_feature_class("rule11")
        assert feature_cls == Rule11Feature

    def test_get_feature_class_not_found(self):
        """获取不存在的 Feature 类"""
        feature_cls = get_feature_class("rule999")
        assert feature_cls is None

    def test_get_score_class_rule8(self):
        """根据规则名获取 Rule8Score"""
        score_cls = get_score_class("rule8")
        assert score_cls == Rule8Score

    def test_get_score_class_not_found(self):
        """获取不存在的 Score 类"""
        score_cls = get_score_class("rule999")
        assert score_cls is None

    def test_dynamic_instantiation(self):
        """动态获取类并实例化"""
        feature_cls = get_feature_class("rule8")
        feature = feature_cls(num_transverse_grooves=5)
        assert isinstance(feature, Rule8Feature)
        assert feature.num_transverse_grooves == 5

        score_cls = get_score_class("rule8")
        score = score_cls(score=4)
        assert isinstance(score, Rule8Score)
        assert score.score == 4
```

---

## 5. 测试用例统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 校验规则测试 | 15 | 对应 15 个校验规则，每个测正常+异常 |
| 可变性测试 | 4 | TireStruct、RuleEvaluation、ImageEvaluation、RibSchemeImpl |
| frozen 测试 | 1 | 模板类 frozen 不可修改 |
| name 提取测试 | 9 | Config/Feature/Score 的 name 提取 + 无 name 字段验证 |
| 注册机制测试 | 6 | get_feature_class / get_score_class / 动态实例化 |
| 方法测试 | 6 | ImageEvaluation 的 get_rule / set_feature / set_score / 总分 |
| **总计** | **~41** | |

---

## 6. conftest.py（共享 fixture）

```python
# tests/unittests/models/conftest.py

import pytest
from src.models.image_models import SmallImage, BigImage, ImageMeta, ImageBiz
from src.models.enums import (
    LevelEnum, RegionEnum, SourceTypeEnum,
    ImageModeEnum, ImageFormatEnum
)
from src.models.rule_models import Rule8Config


@pytest.fixture
def valid_meta():
    """创建合法的 ImageMeta"""
    return ImageMeta(
        width=512, height=512, channels=3,
        mode=ImageModeEnum.RGB, format=ImageFormatEnum.PNG, size=10000
    )


@pytest.fixture
def valid_biz():
    """创建合法的 ImageBiz（小图 + SIDE）"""
    return ImageBiz(
        level=LevelEnum.SMALL,
        region=RegionEnum.SIDE,
        source_type=SourceTypeEnum.ORIGINAL
    )


@pytest.fixture
def valid_small_image(valid_meta, valid_biz):
    """创建合法的 SmallImage"""
    return SmallImage(
        image_base64="data:image/png;base64,iVBORw0KGgo=",
        meta=valid_meta,
        biz=valid_biz
    )


@pytest.fixture
def valid_big_image():
    """创建合法的 BigImage"""
    return BigImage(
        image_base64="data:image/png;base64,iVBORw0KGgo=",
        meta=ImageMeta(
            width=1024, height=512, channels=3,
            mode=ImageModeEnum.RGB, format=ImageFormatEnum.PNG, size=20000
        ),
        biz=ImageBiz(
            level=LevelEnum.BIG,
            source_type=SourceTypeEnum.CONCAT
        )
    )


@pytest.fixture
def rule8_config():
    """创建 Rule8Config"""
    return Rule8Config(
        description="横沟数量约束",
        max_score=4,
        activation_node_name="node4",
        groove_width_center=10.0,
        groove_width_side=8.0
    )
```

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
