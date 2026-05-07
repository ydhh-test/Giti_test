# 数据类使用指南

## 1. 目标

本文档定义 `src/models/` 下所有数据类的使用方式，目标是：

- 统一导入方式
- 明确可变性规则
- 明确运行时填充模式
- 为人和 AI 提供快速查阅入口

本文档是 `docs/plans/models/dataclass_design.md` 的使用侧提炼，不重复生成规范，仅聚焦"怎么用"。

---

## 2. 核心原则

### 2.1 导入直接指向文件

不通过 `__init__.py` 重新导出，所有导入直接指向源文件：

```python
from src.models.enums import LevelEnum, RegionEnum
from src.models.tire_struct import TireStruct
from src.models.image_models import SmallImage, BigImage, ImageEvaluation
from src.models.scheme_models import Symmetry0, RibSchemeImpl
from src.models.rule_models import Rule8Config, get_feature_class
```

### 2.2 可变性由 ConfigDict 控制

| 类 | 可变性 | 原因 |
|----|--------|------|
| TireStruct | `validate_assignment=True` | 运行时修改 flag、err_msg |
| RuleEvaluation | `validate_assignment=True` | 运行时填充 feature、score |
| ImageEvaluation | `validate_assignment=True` | 运行时填充 feature、score、current_score |
| RibSchemeImpl | `validate_assignment=True` | 运行时填充 rib_image 等 |
| 模板类（RibTemplate、StitchingTemplate及其子类） | `frozen=True` | 静态配置，防止误修改 |
| 其他 | 默认不可变 | — |

**规则：**
- 不在未明确要求的类上开启 `validate_assignment`
- 不在模板类上开启 `validate_assignment`（它与 `frozen` 互斥）

### 2.3 name 属性自动提取

RuleConfig / RuleFeature / RuleScore 的 `name` 属性从类名自动提取，不要手动定义字段：

```python
Rule8Config(...).name   # → "rule8"
Rule8Feature(...).name  # → "rule8"
Rule8Score(...).name    # → "rule8"
```

### 2.4 可变默认值使用 Field(default_factory=...)

```python
# ❌ 错误
items: List[str] = []

# ✅ 正确
items: List[str] = Field(default_factory=list)
```

---

## 3. 核心类速查表

### 3.1 接入层

| 类 | 文件 | 用途 | 可变 |
|----|------|------|------|
| TireStruct | tire_struct.py | 所有 Pipeline 的统一入参/出参 | ✅ |

### 3.2 节点层

| 类 | 文件 | 用途 | 可变 |
|----|------|------|------|
| BaseImage | image_models.py | 图像基类（不直接使用） | ❌ |
| SmallImage | image_models.py | 小图（Pipeline-1 入参，Pipeline-4 出参） | ❌ |
| BigImage | image_models.py | 大图（Pipeline-2/3 入参，Pipeline-1/2/3 出参） | ❌ |
| ImageMeta | image_models.py | 图像元信息（宽高、通道等） | ❌ |
| ImageBiz | image_models.py | 图像业务信息（层级、区域、来源） | ❌ |
| ImageEvaluation | image_models.py | 评估结果容器 | ✅ |
| RuleEvaluation | image_models.py | 单规则评估结果 | ✅ |
| ImageScore | image_models.py | 大图评分（与前端格式对齐） | ❌ |
| ImageLineage | image_models.py | 大图血缘信息 | ❌ |

### 3.3 方案层

| 类 | 文件 | 用途 | 可变 |
|----|------|------|------|
| StitchingTemplate | scheme_models.py | 拼接模板基类 | frozen |
| Symmetry0 | scheme_models.py | 拼接模板：无对称 | frozen |
| Symmetry1 | scheme_models.py | 拼接模板：中心旋转180°对称 | frozen |
| Continuity0 | scheme_models.py | 拼接模板：RIB2-3-4全连续 | frozen |
| _Concatenate0 | scheme_models.py | 拼接模板：两张图拼接（内部） | frozen |
| RibTemplate | scheme_models.py | RIB 模板定义 | frozen |
| RibSchemeImpl | scheme_models.py | RIB 拼接方案实现（运行时） | ✅ |
| StitchingScheme | scheme_models.py | 拼接完整方案（运行时） | ❌ |
| StitchingSchemeAbstract | scheme_models.py | 拼接方案摘要 | ❌ |
| MainGrooveScheme | scheme_models.py | 主沟花纹方案 | ❌ |
| DecorationScheme | scheme_models.py | 装饰花纹方案 | ❌ |

### 3.4 规则层

| 类 | 文件 | 用途 | 可变 |
|----|------|------|------|
| BaseRuleConfig | rule_models.py | 规则配置基类 | ❌ |
| BaseRuleFeature | rule_models.py | 规则特征基类 | ❌ |
| BaseRuleScore | rule_models.py | 规则评分基类 | ❌ |
| RuleNConfig | rule_models.py | 各规则配置（22个） | ❌ |
| RuleNFeature | rule_models.py | 各规则特征（22个，需注册） | ❌ |
| RuleNScore | rule_models.py | 各规则评分（22个，需注册） | ❌ |

### 3.5 枚举

| 类 | 文件 | 用途 |
|----|------|------|
| LevelEnum | enums.py | 图像层级：small / big |
| RegionEnum | enums.py | 区域：side / center |
| SourceTypeEnum | enums.py | 来源：original / inherit / concat |
| ImageModeEnum | enums.py | 颜色模式：GRAY / RGB / RGBA |
| ImageFormatEnum | enums.py | 格式：jpg / png / bmp / raw |
| StitchingSchemeName | enums.py | 拼接方案名称 |
| RibOperation | enums.py | RIB 原子操作 |

### 3.6 注册表函数

| 函数 | 文件 | 用途 |
|------|------|------|
| register_rule_feature | rule_models.py | 装饰器：注册 Feature 类 |
| register_rule_score | rule_models.py | 装饰器：注册 Score 类 |
| get_feature_class | rule_models.py | 根据规则名获取 Feature 类 |
| get_score_class | rule_models.py | 根据规则名获取 Score 类 |

---

## 4. 常见使用模式

### 4.1 构造 Pipeline 输入

```python
from src.models.tire_struct import TireStruct
from src.models.image_models import SmallImage, ImageMeta, ImageBiz
from src.models.enums import LevelEnum, RegionEnum, SourceTypeEnum, ImageModeEnum, ImageFormatEnum
from src.models.rule_models import Rule8Config

# 构造小图
small_images = [
    SmallImage(
        image_base64="data:image/png;base64,xxx",
        meta=ImageMeta(width=512, height=512, channels=3, mode=ImageModeEnum.RGB, format=ImageFormatEnum.PNG, size=10000),
        biz=ImageBiz(level=LevelEnum.SMALL, region=RegionEnum.SIDE, source_type=SourceTypeEnum.ORIGINAL),
    ),
]

# 构造输入
tire_struct = TireStruct(
    small_images=small_images,
    rules_config=[Rule8Config(
        description="横沟数量约束",
        max_score=4,
        activation_node_name="node4",
        groove_width_center=10.0,
        groove_width_side=8.0,
    )],
    scheme_rank=1,
    is_debug=True,
)
```

### 4.2 运行时填充 evaluation

```python
from src.models.image_models import ImageEvaluation, RuleEvaluation
from src.models.rule_models import Rule8Feature, Rule8Score

# 创建评估容器
big_image.evaluation = ImageEvaluation(rules=[
    RuleEvaluation(name="rule8", config=rules_config[0]),
])

# 填充 feature
big_image.evaluation.set_feature("rule8", Rule8Feature(num_transverse_grooves=5))

# 填充 score（自动更新 current_score）
big_image.evaluation.set_score("rule8", Rule8Score(score=4))

# 读取总分
print(big_image.evaluation.current_score)  # 4
```

### 4.3 动态获取规则类

```python
from src.models.rule_models import get_feature_class, get_score_class

# 根据规则名获取类
feature_cls = get_feature_class("rule8")   # → Rule8Feature
score_cls = get_score_class("rule8")       # → Rule8Score

# 实例化
feature = feature_cls(num_transverse_grooves=5)
score = score_cls(score=4)
```

### 4.4 访问输出数据

```python
# 访问大图
big_image = tire_struct.big_image

# 访问评估结果
evaluation = big_image.evaluation

# 获取某个规则的评估结果
rule8_result = evaluation.get_rule("rule8")

# 访问特征和评分
feature = rule8_result.feature
score = rule8_result.score

# 访问总分
total_score = evaluation.current_score
```

### 4.5 Debug 可视化

```python
# 开启 debug
tire_struct.is_debug = True

# Feature 中填充可视化数据
feature.vis_names = ["原始图", "检测结果图"]
feature.vis_images = ["base64_1", "base64_2"]
```

---

## 5. 校验规则

### 5.1 Field 约束（自动校验）

| 类 | 字段 | 约束 |
|----|------|------|
| ImageMeta | width, height | >= 1 |
| ImageMeta | channels | 1 ~ 4 |
| ImageMeta | size | >= 0 |
| DecorationImpl | decoration_opacity | 0 ~ 255 |
| Rule17Config | edge_continuity_rib1_rib2, edge_continuity_rib4_rib5 | 0 ~ 1 |
| Rule8Config | groove_width_center, groove_width_side | > 0 |

### 5.2 model_validator 校验（实例化时触发）

| 类 | 规则 | 错误信息 |
|----|------|---------|
| TireStruct | 必须有小图或大图 | "必须输入小图或大图，流程无法执行" |
| TireStruct | scheme_rank >= 1 | "方案排名必须>=1" |
| BaseImage | base64 必须含 data:image/ 前缀 | "image_base64必须包含data:image/*;base64,前缀" |
| ImageMeta | width/height <= 10000 | "图像尺寸超过上限10000像素" |
| ImageBiz | 原始数据必须有 region | "原始数据必须指定region" |
| ImageBiz | 继承来源必须有 inherit_from | "继承来源必须指定inherit_from" |
| ImageEvaluation | 规则名称不能重复 | "规则名称不能重复" |
| RuleEvaluation | feature/score 的 name 必须与 rule name 一致 | "feature.name != rule name" |
| RibSchemeImpl | 最外层 RIB 必须有 rib_name | "最外层RIB必须有rib_name" |
| RibSchemeImpl | 继承来源必须有 inherit_from | "继承来源必须指定inherit_from" |

---

## 6. 扩展指南

### 6.1 新增规则

1. 在 `rule_models.py` 中添加三个类：

```python
class Rule23Config(BaseRuleConfig):
    """Rule23：新规则描述"""
    description: str = "新规则描述"
    max_score: int = 4
    activation_node_name: str = "node_x"
    # 业务字段...

@register_rule_feature
class Rule23Feature(BaseRuleFeature):
    """Rule23特征"""
    # 特征字段...

@register_rule_score
class Rule23Score(BaseRuleScore):
    """Rule23评分"""
    pass
```

2. Feature 和 Score 必须加注册装饰器
3. 注册后即可通过 `get_feature_class("rule23")` / `get_score_class("rule23")` 获取

### 6.2 新增拼接模板

1. 在 `StitchingSchemeName` 枚举中添加名称
2. 在 `scheme_models.py` 中添加模板类（继承 `StitchingTemplate`，`frozen=True`）
3. 如需子模板展开，使用 `sub_template_name` 字段

---

## 7. 常见错误

### 7.1 可变默认值

```python
# ❌ 错误
class MyModel(BaseModel):
    items: List[str] = []

# ✅ 正确
class MyModel(BaseModel):
    items: List[str] = Field(default_factory=list)
```

### 7.2 运行时修改不可变对象

```python
# ❌ 错误（默认不可变）
meta = ImageMeta(width=512, ...)
meta.width = 1024  # ValidationError

# ✅ 方案1：重新构造
meta = ImageMeta(width=1024, ...)

# ✅ 方案2：使用 model_copy
meta = meta.model_copy(update={"width": 1024})
```

### 7.3 手动定义 name 字段

```python
# ❌ 错误
class Rule8Config(BaseRuleConfig):
    name: str = "rule8"  # 与 @property name 冲突

# ✅ 正确（name 从类名自动提取）
class Rule8Config(BaseRuleConfig):
    pass

Rule8Config(...).name  # → "rule8"
```

### 7.4 忘记注册装饰器

```python
# ❌ 错误（get_feature_class("rule8") 返回 None）
class Rule8Feature(BaseRuleFeature):
    pass

# ✅ 正确
@register_rule_feature
class Rule8Feature(BaseRuleFeature):
    pass
```

---

## 8. 与项目规范的关系

本文档是 `docs/plans/models/dataclass_design.md` 的使用侧提炼：
- **dataclass_design.md**：面向 AI 执行代码生成，包含完整代码模板和约束检查表
- **本文档**：面向人和 AI 日常使用，聚焦"怎么用"

执行时仍应同时遵守：
- `docs/project_coding_standards.md`
- `docs/project_coding_standards_agent.md`

---

**文档结束**
