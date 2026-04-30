# Fake Generation API 设计文档

## 版本信息
- 文档版本：v1.0
- 创建日期：2026-04-23
- 状态：Draft

---

## 一、设计目标

### 1.1 核心目标
本次设计目标是实现一个 **fake API**，用于验证调用方是否能按期望结构发送输入数据。

### 1.2 具体目标
1. 冻结 `generation` 接口的输入输出协议
2. 验证两层嵌套数据结构的合理性
3. 测试调用方能否正确构造输入对象
4. 降低后续交互设计风险

### 1.3 非目标
- 不实现真实业务流程
- 不调用 nodes / rules / core
- 不实现算法或规则逻辑
- 不支持 `is_debug=True` 场景

---

## 二、设计原则

### 2.1 文件级隔离
- fake 代码与正式代码文件分离
- model 层也使用 fake 文件

### 2.2 使用 Pydantic
- 所有数据类继承 `pydantic.BaseModel`
- 自动序列化/反序列化（`model_dump()` / `model_validate()`）
- 使用 `@field_validator` 和 `@model_validator` 进行校验
- 结构化错误信息

### 2.3 严格校验模式
- 多一个字段、少一个字段都视为失败
- 类型不匹配立即失败
- 值范围不符合立即失败

### 2.4 薄层 API 设计
- API 层只负责调用 pydantic 校验和构造响应
- 校验逻辑在模型层通过 validator 实现

---

## 三、文件结构

### 3.1 文件清单

```
version.json                           # 项目版本文件
src/
├── api/
│   └── fake_generation.py          # fake API 入口
│
└── models/
    ├── fake_tire_struct.py         # 顶层聚合对象
    ├── fake_image_models.py        # 图像相关模型
    ├── fake_rules_models.py        # 规则相关模型
    └── fake_result_models.py       # 结果相关模型
```

### 3.2 文件职责

| 文件 | 职责 |
|------|------|
| `version.json` | 项目版本信息，调用方读取进行版本比对 |
| `fake_generation.py` | API 入口，输入校验，响应构造 |
| `fake_tire_struct.py` | API 顶层输入输出对象 |
| `fake_image_models.py` | 所有图像相关模型 |
| `fake_rules_models.py` | 所有规则配置相关模型 |
| `fake_result_models.py` | 所有输出结果相关模型 |

---

## 四、数据模型设计

### 4.1 技术选型

使用 **pydantic v2** 作为数据模型框架：

| 特性 | 说明 |
|------|------|
| 序列化 | `model.model_dump()` → dict |
| 反序列化 | `Model(**data)` 或 `Model.model_validate(data)` |
| JSON 序列化 | `model.model_dump_json()` → JSON 字符串 |
| JSON 反序列化 | `Model.model_validate_json(json_str)` |
| 校验 | `@field_validator` 字段级校验<br>`@model_validator` 模型级校验 |
| 错误处理 | `ValidationError` 结构化错误信息 |

### 4.2 类清单汇总

共 19 个 pydantic 模型类（含 2 个基类），按文件归类：

| 文件 | 类 |
|------|-----|
| `fake_result_models.py` | `FakeFeatureResult`<br>`FakeEvaluation`<br>`FakeScoreResult`<br>`FakeLineage` |
| `fake_image_models.py` | `FakeImageMeta`<br>`FakeSmallImageBiz`<br>`FakeBigImageBiz`<br>`FakeBaseImage`（基类）<br>`FakeSmallImage`<br>`FakeBigImage` |
| `fake_rules_models.py` | `FakeGroovesWidthMm`<br>`FakeRule6_1Config`<br>`FakeRule8Config`<br>`FakeRuleConfigBase`（基类）<br>`FakeRule6_1`<br>`FakeRule8`<br>`FakeRulesConfig` |
| `fake_tire_struct.py` | `FakeTireStruct` |

**说明**：使用基类减少重复字段定义，`FakeBaseImage` 和 `FakeRuleConfigBase` 分别作为图像类和规则类的公共基类。

---

### 4.3 类关系图

```
FakeTireStruct (BaseModel)
├── small_images: List[FakeSmallImage]
├── big_image: FakeBigImage | None
├── rules_config: FakeRulesConfig
├── scheme_rank: int
├── is_debug: bool
├── flag: bool
├── err_code: str | None
└── err_msg: str | None

FakeBaseImage (BaseModel) ←── 基类
├── image_base64: str
├── meta: FakeImageMeta
└── evaluation: FakeEvaluation
    ↑
    ├── FakeSmallImage
    │   └── biz: FakeSmallImageBiz
    │
    └── FakeBigImage
        ├── biz: FakeBigImageBiz
        ├── scores: List[FakeScoreResult]
        └── lineage: FakeLineage

FakeRuleConfigBase (BaseModel) ←── 基类
├── rule_name: str
├── description: str
└── score: float
    ↑
    ├── FakeRule6_1
    │   └── rule_config: FakeRule6_1Config
    │
    └── FakeRule8
        └── rule_config: FakeRule8Config

FakeRulesConfig (BaseModel)
├── rule6_1: FakeRule6_1
└── rule8: FakeRule8
```

---

### 4.4 详细字段定义

#### 4.4.1 `fake_result_models.py`

---

**FakeFeatureResult** - 评分依据/特征结果

```python
from pydantic import BaseModel, field_validator

class FakeFeatureResult(BaseModel):
    rule_name: str
    feature_name: str
    feature_value: str
    description: str
    
    @field_validator('rule_name')
    @classmethod
    def validate_rule_name(cls, v: str) -> str:
        if v not in ("rule6-1", "rule8"):
            raise ValueError("rule_name must be 'rule6-1' or 'rule8'")
        return v
```

---

**FakeEvaluation** - 评估结果集合

```python
from pydantic import BaseModel, Field
from typing import List

class FakeEvaluation(BaseModel):
    features: List[FakeFeatureResult] = Field(default_factory=list)
```

---

**FakeScoreResult** - 评分结果项

```python
from pydantic import BaseModel, field_validator

class FakeScoreResult(BaseModel):
    rule_name: str
    description: str
    score_value: float
    score_max: float
    reason: str
    
    @field_validator('rule_name')
    @classmethod
    def validate_rule_name(cls, v: str) -> str:
        if v not in ("rule6-1", "rule8"):
            raise ValueError("rule_name must be 'rule6-1' or 'rule8'")
        return v
    
    @field_validator('score_value')
    @classmethod
    def validate_score_value(cls, v: float, info) -> float:
        # 需要在 model_validator 中校验 score_value <= score_max
        return v
```

---

**FakeLineage** - 大图血缘信息

```python
from pydantic import BaseModel, Field
from typing import List

class FakeLineage(BaseModel):
    source_image_ids: List[str] = Field(default_factory=list)
    scheme_rank: int
    summary: str
```

---

#### 4.4.2 `fake_image_models.py`

---

**FakeImageMeta** - 图像元信息

```python
from pydantic import BaseModel, field_validator

class FakeImageMeta(BaseModel):
    width: int
    height: int
    channel: int

    @field_validator('width', 'height', 'channel')
    @classmethod
    def validate_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("must be positive")
        return v
```

---

**FakeSmallImageBiz** - 小图业务信息

```python
from pydantic import BaseModel, field_validator
from typing import Optional

class FakeSmallImageBiz(BaseModel):
    image_id: str
    position: Optional[str] = None
    camera_id: Optional[str] = None

    @field_validator('image_id')
    @classmethod
    def validate_image_id(cls, v: str) -> str:
        if not v:
            raise ValueError("image_id must not be empty")
        return v
```

---

**FakeBigImageBiz** - 大图业务信息

```python
from pydantic import BaseModel, field_validator

class FakeBigImageBiz(BaseModel):
    image_id: str
    scheme_rank: int
    status: str

    @field_validator('image_id')
    @classmethod
    def validate_image_id(cls, v: str) -> str:
        if not v:
            raise ValueError("image_id must not be empty")
        return v
```

---

**FakeBaseImage** - 图像基类

```python
from pydantic import BaseModel, field_validator

class FakeBaseImage(BaseModel):
    """图像基类，定义公共字段。"""
    image_base64: str
    meta: "FakeImageMeta"
    evaluation: "FakeEvaluation"

    @field_validator('image_base64')
    @classmethod
    def validate_image_base64(cls, v: str) -> str:
        if not v:
            raise ValueError("image_base64 must not be empty")
        return v
```

---

**FakeSmallImage** - 小图对象

```python
from pydantic import BaseModel

class FakeSmallImage(FakeBaseImage):
    """小图对象，继承 FakeBaseImage。"""
    biz: "FakeSmallImageBiz"
```

---

**FakeBigImage** - 大图对象

```python
from pydantic import BaseModel, Field
from typing import List

class FakeBigImage(FakeBaseImage):
    """大图对象，继承 FakeBaseImage。"""
    biz: "FakeBigImageBiz"
    scores: List["FakeScoreResult"] = Field(default_factory=list)
    lineage: "FakeLineage"
```

---

#### 4.4.3 `fake_rules_models.py`

---

**FakeGroovesWidthMm** - 横沟宽度配置

```python
from pydantic import BaseModel, field_validator

class FakeGroovesWidthMm(BaseModel):
    center: float
    side: float

    @field_validator('center', 'side')
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("must be positive")
        return v
```

---

**FakeRule6_1Config** - rule6-1 配置

```python
from pydantic import BaseModel

class FakeRule6_1Config(BaseModel):
    gray_threshold_lte: int
```

---

**FakeRule8Config** - rule8 配置

```python
from pydantic import BaseModel, field_validator

class FakeRule8Config(BaseModel):
    grooves_width_mm: FakeGroovesWidthMm
    grooves_lte: int

    @field_validator('grooves_lte')
    @classmethod
    def validate_grooves_lte(cls, v: int) -> int:
        if v < 0:
            raise ValueError("must be non-negative")
        return v
```

---

**FakeRuleConfigBase** - 规则配置基类

```python
from pydantic import BaseModel, field_validator

class FakeRuleConfigBase(BaseModel):
    """规则配置基类，定义公共字段。"""
    rule_name: str
    description: str
    score: float

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        if v < 0:
            raise ValueError("score must be non-negative")
        return v
```

---

**FakeRule6_1** - rule6-1 规则对象

```python
from pydantic import BaseModel, model_validator

class FakeRule6_1(FakeRuleConfigBase):
    """rule6-1 规则对象，继承 FakeRuleConfigBase。"""
    rule_config: FakeRule6_1Config

    @model_validator(mode='after')
    def validate_rule_name(self):
        if self.rule_name != "rule6-1":
            raise ValueError("rule_name must be 'rule6-1'")
        return self
```

---

**FakeRule8** - rule8 规则对象

```python
from pydantic import BaseModel, model_validator

class FakeRule8(FakeRuleConfigBase):
    """rule8 规则对象，继承 FakeRuleConfigBase。"""
    rule_config: FakeRule8Config

    @model_validator(mode='after')
    def validate_rule_name(self):
        if self.rule_name != "rule8":
            raise ValueError("rule_name must be 'rule8'")
        return self
```

---

**FakeRulesConfig** - 规则配置集合

```python
from pydantic import BaseModel

class FakeRulesConfig(BaseModel):
    rule6_1: FakeRule6_1
    rule8: FakeRule8
```

---

#### 4.4.4 `fake_tire_struct.py`

---

**FakeTireStruct** - API 顶层聚合对象

```python
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

class FakeTireStruct(BaseModel):
    small_images: List[FakeSmallImage] = Field(default_factory=list)
    big_image: Optional[FakeBigImage] = None
    rules_config: FakeRulesConfig
    scheme_rank: int
    is_debug: bool = False
    flag: bool = False
    err_code: Optional[str] = None
    err_msg: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_request(self):
        """校验请求状态：输入时的约束。"""
        if len(self.small_images) == 0:
            raise ValueError("small_images must not be empty")
        if self.big_image is not None:
            raise ValueError("big_image must be None in request")
        if self.scheme_rank < 1:
            raise ValueError("scheme_rank must be >= 1")
        if self.is_debug:
            raise ValueError("is_debug must be False in current fake API")
        if self.flag:
            raise ValueError("flag must be False in request")
        if self.err_code is not None:
            raise ValueError("err_code must be None in request")
        if self.err_msg is not None:
            raise ValueError("err_msg must be None in request")
        return self
```

---

---

## 五、Pydantic 使用说明

### 5.1 安装依赖

```bash
pip install pydantic
```

### 5.2 基本用法

```python
from pydantic import BaseModel, ValidationError

# 从 dict 构造对象（自动校验）
try:
    tire_struct = FakeTireStruct(**data)
except ValidationError as e:
    # 处理校验错误
    errors = e.errors()
    # errors 是列表，每个元素包含: {'loc': (), 'msg': '', 'type': ''}

# 转为 dict
result_dict = tire_struct.model_dump()

# 转为 JSON 字符串
result_json = tire_struct.model_dump_json()

# 从 JSON 字符串构造
tire_struct = FakeTireStruct.model_validate_json(json_str)
```

### 5.3 错误处理

```python
from pydantic import ValidationError

def generate_big_image_with_evaluation(data: dict) -> dict:
    """API 入口函数。"""
    try:
        # 构造并校验
        tire_struct = FakeTireStruct(**data)
        
        # 返回成功响应
        return create_success_response(tire_struct).model_dump()
    
    except ValidationError as e:
        # 提取第一个错误
        errors = e.errors()
        if errors:
            err_msg = errors[0]['msg']
        else:
            err_msg = str(e)
        
        # 返回失败响应
        return {
            "small_images": data.get("small_images", []),
            "big_image": None,
            "rules_config": data.get("rules_config"),
            "scheme_rank": data.get("scheme_rank", 1),
            "is_debug": data.get("is_debug", False),
            "flag": False,
            "err_code": "DATA_ERROR",
            "err_msg": err_msg,
        }
```

### 5.4 校验器说明

| 校验器 | 用途 | 示例 |
|--------|------|------|
| `@field_validator` | 单字段校验 | 校验 `width > 0` |
| `@model_validator` | 多字段联合校验 | 校验 `rule_name == "rule6-1"` |

### 5.5 前向引用

由于类之间存在循环引用，需要使用前向引用（字符串形式的类型名）：

```python
from typing import List

class FakeBigImage(BaseModel):
    # ...
    scores: List["FakeScoreResult"] = Field(default_factory=list)
    lineage: "FakeLineage"
```

---

## 六、API 设计

### 6.1 主函数签名

```python
def generate_big_image_with_evaluation(data: dict) -> dict:
    """
    Fake API: 根据小图生成大图并返回评分结果。
    
    本函数仅用于验证输入输出协议，不实现真实流程。
    
    Args:
        data: 输入字典
    
    Returns:
        dict: 成功或失败响应（字典格式）
    """
```

### 6.2 函数实现逻辑

```python
from pydantic import ValidationError

def generate_big_image_with_evaluation(data: dict) -> dict:
    """Fake API 入口。"""
    try:
        # 构造并校验（pydantic 自动执行）
        tire_struct = FakeTireStruct(**data)
        
        # 返回成功响应
        return create_success_response(tire_struct).model_dump()
    
    except ValidationError as e:
        # 提取错误信息
        return create_error_response_from_data(data, e)
```

### 6.3 辅助函数

#### create_error_response_from_data

```python
def create_error_response_from_data(data: dict, error: ValidationError) -> dict:
    """从原始数据和校验错误构造失败响应。"""
    errors = error.errors()
    if errors:
        # 提取第一个错误信息
        err_msg = errors[0]['msg']
    else:
        err_msg = str(error)
    
    return {
        "small_images": data.get("small_images", []),
        "big_image": None,
        "rules_config": data.get("rules_config"),
        "scheme_rank": data.get("scheme_rank", 1),
        "is_debug": data.get("is_debug", False),
        "flag": False,
        "err_code": "DATA_ERROR",
        "err_msg": err_msg,
    }
```

#### create_success_response

```python
def create_success_response(original: FakeTireStruct) -> FakeTireStruct:
    """构造成功响应对象（fake 固定输出）。"""
    # 收集来源小图 ID
    source_image_ids = [img.biz.image_id for img in original.small_images]
    
    # 构造 fake big_image
    big_image = FakeBigImage(
        image_base64="data:image/png;base64,FAKE_BIG_IMAGE_PLACEHOLDER",
        meta=FakeImageMeta(
            width=1024,
            height=512,
            channel=3,
        ),
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
            ],
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
    
    return FakeTireStruct(
        small_images=original.small_images,
        big_image=big_image,
        rules_config=original.rules_config,
        scheme_rank=original.scheme_rank,
        is_debug=original.is_debug,
        flag=True,
        err_code=None,
        err_msg=None,
    )
```

---

## 七、校验规则汇总

### 7.1 错误码定义

| 错误码 | 类别 | 说明 |
|--------|------|------|
| `DATA_ERROR` | 数据错误 | 输入数据校验失败（缺少字段、类型错误、值范围错误等） |
| `RUNTIME_ERROR` | 运行时错误 | 代码执行出错（内部异常） |

### 7.2 顶层字段校验规则

| 字段 | 校验规则 | 错误信息 |
|------|----------|----------|
| `small_images` | 必填，list，非空 | `small_images is required`<br>`small_images must be a list`<br>`small_images must not be empty` |
| `big_image` | 输入时必须为 None | `big_image must be None in request` |
| `rules_config` | 必填，FakeRulesConfig | `rules_config is required`<br>`rules_config must be FakeRulesConfig` |
| `scheme_rank` | 必填，int，>= 1 | `scheme_rank is required`<br>`scheme_rank must be int`<br>`scheme_rank must be greater than or equal to 1` |
| `is_debug` | 必填，bool，必须为 False | `is_debug is required`<br>`is_debug must be bool`<br>`is_debug must be False in current fake API` |
| `flag` | 必填，bool，输入时必须为 False | `flag is required`<br>`flag must be bool`<br>`flag must be False in request` |
| `err_code` | 必填，str 或 None，输入时必须为 None | `err_code is required`<br>`err_code must be str or None`<br>`err_code must be None in request` |
| `err_msg` | 必填，str 或 None，输入时必须为 None | `err_msg is required`<br>`err_msg must be str or None`<br>`err_msg must be None in request` |

### 7.3 规则约束

| 规则 | 约束 |
|------|------|
| rule_name | `FakeFeatureResult` 和 `FakeScoreResult` 的 `rule_name` 只允许 `"rule6-1"` 或 `"rule8"` |
| FakeRule6_1.rule_name | 必须等于 `"rule6-1"` |
| FakeRule8.rule_name | 必须等于 `"rule8"` |
| FakeRulesConfig | 只包含 `rule6_1` 和 `rule8`，采用固定字段 |

---

## 八、输入输出样例

### 8.1 成功输入样例

```python
FakeTireStruct(
    small_images=[
        FakeSmallImage(
            image_base64="data:image/png;base64,AAA...",
            meta=FakeImageMeta(width=512, height=512, channel=3),
            biz=FakeSmallImageBiz(image_id="small-001", position="left", camera_id="cam-01"),
            evaluation=FakeEvaluation(features=[]),
        ),
        FakeSmallImage(
            image_base64="data:image/png;base64,BBB...",
            meta=FakeImageMeta(width=512, height=512, channel=3),
            biz=FakeSmallImageBiz(image_id="small-002", position="right", camera_id="cam-01"),
            evaluation=FakeEvaluation(features=[]),
        ),
    ],
    big_image=None,
    rules_config=FakeRulesConfig(
        rule6_1=FakeRule6_1(
            rule_name="rule6-1",
            description="图案连续性检测",
            score=10,
            rule_config=FakeRule6_1Config(gray_threshold_lte=200),
        ),
        rule8=FakeRule8(
            rule_name="rule8",
            description="横沟数量检测",
            score=4,
            rule_config=FakeRule8Config(
                grooves_width_mm=FakeGroovesWidthMm(center=3.5, side=1.8),
                grooves_lte=1,
            ),
        ),
    ),
    scheme_rank=1,
    is_debug=False,
    flag=False,
    err_code=None,
    err_msg=None,
)
```

### 8.2 成功输出样例

```python
FakeTireStruct(
    small_images=[...],  # 原样保留
    big_image=FakeBigImage(
        image_base64="data:image/png;base64,FAKE_BIG_IMAGE_PLACEHOLDER",
        meta=FakeImageMeta(width=1024, height=512, channel=3),
        biz=FakeBigImageBiz(image_id="big-001", scheme_rank=1, status="generated"),
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
            ],
        ),
        scores=[
            FakeScoreResult(
                rule_name="rule6-1",
                description="图案连续性检测",
                score_value=8.0,
                score_max=10.0,
                reason="连续性基本满足要求",
            ),
            FakeScoreResult(
                rule_name="rule8",
                description="横沟数量检测",
                score_value=4.0,
                score_max=4.0,
                reason="横沟数量满足要求",
            ),
        ],
        lineage=FakeLineage(
            source_image_ids=["small-001", "small-002"],
            scheme_rank=1,
            summary="由 2 张小图按第 1 名方案生成大图",
        ),
    ),
    rules_config=...,  # 原样保留
    scheme_rank=1,
    is_debug=False,
    flag=True,
    err_code=None,
    err_msg=None,
)
```

### 8.3 失败输出样例

```python
FakeTireStruct(
    small_images=[...],  # 原样保留
    big_image=None,
    rules_config=...,  # 原样保留
    scheme_rank=1,
    is_debug=False,
    flag=False,
    err_code="DATA_ERROR",
    err_msg="small_images must not be empty",
)
```

---

## 九、错误样例集

建议测试时至少覆盖以下错误场景：

| 编号 | 错误场景 | 预期错误码 | 预期错误信息 |
|------|----------|------------|--------------|
| E1 | `small_images=[]` | `DATA_ERROR` | `small_images must not be empty` |
| E2 | `big_image` 非空 | `DATA_ERROR` | `big_image must be None in request` |
| E3 | 缺 `rule6_1` | `DATA_ERROR` | `rules_config: rule6_1 is required` |
| E4 | 缺 `rule8` | `DATA_ERROR` | `rules_config: rule8 is required` |
| E5 | `scheme_rank=0` | `DATA_ERROR` | `scheme_rank must be greater than or equal to 1` |
| E6 | `is_debug=True` | `DATA_ERROR` | `is_debug must be False in current fake API` |
| E7 | `flag=True` | `DATA_ERROR` | `flag must be False in request` |
| E8 | `err_code="xxx"` | `DATA_ERROR` | `err_code must be None in request` |
| E9 | `err_msg="xxx"` | `DATA_ERROR` | `err_msg must be None in request` |
| E10 | `rule6_1.rule_name="wrong"` | `DATA_ERROR` | `rules_config.rule6_1: rule_name must be 'rule6-1'` |
| E11 | `rule8.rule_name="wrong"` | `DATA_ERROR` | `rules_config.rule8: rule_name must be 'rule8'` |

---

## 十、依赖关系

### 10.1 文件依赖

```
fake_tire_struct.py
    ├── fake_image_models.py
    │       └── fake_result_models.py
    └── fake_rules_models.py
```

### 10.2 导入关系

#### fake_result_models.py

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List
```

无其他 fake model 依赖。

---

#### fake_image_models.py

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

from .fake_result_models import (
    FakeEvaluation,
    FakeScoreResult,
    FakeLineage,
)
```

---

#### fake_rules_models.py

```python
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
```

无其他 fake model 依赖。

---

#### fake_tire_struct.py

```python
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

from .fake_image_models import (
    FakeSmallImage,
    FakeBigImage,
)
from .fake_rules_models import FakeRulesConfig
```

---

#### fake_generation.py

```python
from pydantic import ValidationError

from ..models.fake_tire_struct import FakeTireStruct
from ..models.fake_image_models import (
    FakeImageMeta,
    FakeSmallImageBiz,
    FakeBigImageBiz,
    FakeBigImage,
)
from ..models.fake_rules_models import (
    FakeRulesConfig,
    FakeRule6_1,
    FakeRule8,
)
from ..models.fake_result_models import (
    FakeFeatureResult,
    FakeEvaluation,
    FakeScoreResult,
    FakeLineage,
)
```

---

### 10.3 与架构的关系

本次设计符合 `ARCHITECTURE.md` 的以下要求：

| 架构要求 | 本次设计 |
|----------|----------|
| API 层薄层化 | API 函数只处理 ValidationError 和构造响应 |
| 模型集中定义 | 所有 fake model 在 `src/models/` 下 |
| 不调用 nodes/rules/core | fake API 不调用下层 |
| 输入输出协议管理 | 通过 `FakeTireStruct` 统一管理 |
| 测试分层 | API 测试放 `tests/integrations`，模型测试放 `tests/unittests` |

---

## 十一、实现建议

### 11.1 实现顺序

1. 安装依赖：`pip install pydantic`
2. 实现 `fake_result_models.py`（无依赖）
   - 定义 pydantic 模型类
   - 添加 `@field_validator` 和 `@model_validator`
3. 实现 `fake_image_models.py`（依赖 fake_result_models）
   - 定义 pydantic 模型类
   - 添加校验器
4. 实现 `fake_rules_models.py`（无依赖）
   - 定义 pydantic 模型类
   - 添加校验器
5. 实现 `fake_tire_struct.py`（依赖 fake_image_models 和 fake_rules_models）
   - 定义顶层模型类
   - 添加 `@model_validator` 进行请求状态校验
6. 实现 `fake_generation.py`
   - 主函数（处理 ValidationError）
   - 辅助函数（构造成功/失败响应）
7. 创建 `version.json` 版本文件

### 11.2 测试策略

**测试框架**：使用 pytest

**测试结构**：

| 测试类型 | 位置 | 内容 |
|----------|------|------|
| 模型单元测试 | `tests/unittests/models/` | 每个模型的校验器（合法值、非法值、边界值） |
| API 集成测试 | `tests/integrations/` | 成功输入、失败输入场景 |
| 样例数据 | `tests/datasets/` | 标准 fake 输入样例 |

**覆盖率要求**：
- 目标：80% 以上
- 重点覆盖：
  - 所有 `@field_validator` 的分支
  - 所有 `@model_validator` 的分支
  - API 入口函数的成功和失败路径
  - 序列化/反序列化正确性

### 11.3 后续扩展方向

1. 支持 `is_debug=True` 场景
2. 扩展更多规则（rule9, rule10, ...）
3. 替换为真实节点实现
4. 接入 `src.rules` 和 `src.core`

---

## 十二、总结

### 12.1 设计成果

1. 4 个 fake model 文件，19 个 pydantic 模型类（含 2 个基类）
2. 1 个 fake API 文件，1 个主函数
3. 基于 pydantic 的自动校验体系
4. 自动序列化/反序列化支持
5. 两级错误码设计
6. 标准输入输出样例
7. 错误场景覆盖
8. 版本管理文件
9. 完整测试代码样例

### 12.2 设计特点

| 特点 | 说明 |
|------|------|
| Pydantic v2 | 自动校验、序列化、反序列化 |
| 强类型 | 不留 dict，全部用 pydantic 模型类 |
| 基类继承 | `FakeBaseImage` 和 `FakeRuleConfigBase` 减少重复定义 |
| 文件隔离 | fake 代码与正式代码分离 |
| 校验器 | `@field_validator` 字段级校验<br>`@model_validator` 模型级校验 |
| 错误码分类 | 两级错误码：`DATA_ERROR` 和 `RUNTIME_ERROR` |
| 严格模式 | 多一个少一个字段都失败 |
| 只支持两条规则 | rule6-1 和 rule8 |
| 版本管理 | 项目根目录 `version.json`，当前版本 `2.0.0` |
| 完整测试覆盖 | 单元测试 + 集成测试样例 |

### 12.3 核心价值

本次设计为后续开发提供：
1. **协议基准**：冻结输入输出结构
2. **联调基础**：调用方可基于 fake API 验证
3. **测试框架**：标准样例和错误场景
4. **架构验证**：验证分层设计的合理性

---

## 附录 A：完整类字段速查表

### fake_result_models.py

| 类 | 字段 | 类型 | 必填 | 默认值 |
|----|------|------|------|--------|
| FakeFeatureResult | rule_name | str | 是 | - |
| FakeFeatureResult | feature_name | str | 是 | - |
| FakeFeatureResult | feature_value | str | 是 | - |
| FakeFeatureResult | description | str | 是 | - |
| FakeEvaluation | features | List[FakeFeatureResult] | 是 | [] |
| FakeScoreResult | rule_name | str | 是 | - |
| FakeScoreResult | description | str | 是 | - |
| FakeScoreResult | score_value | float | 是 | - |
| FakeScoreResult | score_max | float | 是 | - |
| FakeScoreResult | reason | str | 是 | - |
| FakeLineage | source_image_ids | List[str] | 是 | [] |
| FakeLineage | scheme_rank | int | 是 | - |
| FakeLineage | summary | str | 是 | - |

### fake_image_models.py

| 类 | 字段 | 类型 | 必填 | 默认值 |
|----|------|------|------|--------|
| FakeImageMeta | width | int | 是 | - |
| FakeImageMeta | height | int | 是 | - |
| FakeImageMeta | channel | int | 是 | - |
| FakeSmallImageBiz | image_id | str | 是 | - |
| FakeSmallImageBiz | position | Optional[str] | 否 | None |
| FakeSmallImageBiz | camera_id | Optional[str] | 否 | None |
| FakeBigImageBiz | image_id | str | 是 | - |
| FakeBigImageBiz | scheme_rank | int | 是 | - |
| FakeBigImageBiz | status | str | 是 | - |
| FakeBaseImage | image_base64 | str | 是 | - |
| FakeBaseImage | meta | FakeImageMeta | 是 | - |
| FakeBaseImage | evaluation | FakeEvaluation | 是 | - |
| FakeSmallImage | biz | FakeSmallImageBiz | 是 | - |
| FakeBigImage | biz | FakeBigImageBiz | 是 | - |
| FakeBigImage | scores | List[FakeScoreResult] | 是 | [] |
| FakeBigImage | lineage | FakeLineage | 是 | - |

### fake_rules_models.py

| 类 | 字段 | 类型 | 必填 | 默认值 |
|----|------|------|------|--------|
| FakeGroovesWidthMm | center | float | 是 | - |
| FakeGroovesWidthMm | side | float | 是 | - |
| FakeRule6_1Config | gray_threshold_lte | int | 是 | - |
| FakeRule8Config | grooves_width_mm | FakeGroovesWidthMm | 是 | - |
| FakeRule8Config | grooves_lte | int | 是 | - |
| FakeRuleConfigBase | rule_name | str | 是 | - |
| FakeRuleConfigBase | description | str | 是 | - |
| FakeRuleConfigBase | score | float | 是 | - |
| FakeRule6_1 | rule_config | FakeRule6_1Config | 是 | - |
| FakeRule8 | rule_config | FakeRule8Config | 是 | - |
| FakeRulesConfig | rule6_1 | FakeRule6_1 | 是 | - |
| FakeRulesConfig | rule8 | FakeRule8 | 是 | - |

### fake_tire_struct.py

| 类 | 字段 | 类型 | 必填 | 默认值 |
|----|------|------|------|--------|
| FakeTireStruct | small_images | List[FakeSmallImage] | 是 | [] |
| FakeTireStruct | big_image | FakeBigImage \| None | 是 | None |
| FakeTireStruct | rules_config | FakeRulesConfig | 是 | - |
| FakeTireStruct | scheme_rank | int | 是 | - |
| FakeTireStruct | is_debug | bool | 是 | False |
| FakeTireStruct | flag | bool | 是 | False |
| FakeTireStruct | err_code | str \| None | 是 | None |
| FakeTireStruct | err_msg | str \| None | 是 | None |

---

## 附录 B：校验器速查表

| 类 | 校验器类型 | 校验内容 |
|----|------------|----------|
| FakeTireStruct | `@model_validator` | small_images 非空、big_image 为 None、scheme_rank >= 1、is_debug 为 False、flag 为 False、err_code 为 None、err_msg 为 None |
| FakeBaseImage | `@field_validator` | image_base64 非空 |
| FakeSmallImage | 继承 FakeBaseImage | 继承 image_base64 校验 |
| FakeBigImage | 继承 FakeBaseImage | 继承 image_base64 校验 |
| FakeImageMeta | `@field_validator` | width/height/channel > 0 |
| FakeSmallImageBiz | `@field_validator` | image_id 非空 |
| FakeBigImageBiz | `@field_validator` | image_id 非空 |
| FakeFeatureResult | `@field_validator` | rule_name 在 ["rule6-1", "rule8"] 中 |
| FakeScoreResult | `@field_validator` | rule_name 在 ["rule6-1", "rule8"] 中 |
| FakeRuleConfigBase | `@field_validator` | score >= 0 |
| FakeRule6_1 | 继承 + `@model_validator` | 继承 score 校验、rule_name == "rule6-1" |
| FakeRule8 | 继承 + `@model_validator` | 继承 score 校验、rule_name == "rule8" |
| FakeRule8Config | `@field_validator` | grooves_lte >= 0 |
| FakeGroovesWidthMm | `@field_validator` | center > 0、side > 0 |

---

## 附录 C：版本文件

### 位置

项目根目录：`version.json`

### 内容

```json
{
  "version": "2.0.0",
  "description": "Fake Generation API - Protocol Validation",
  "updated_at": "2026-04-23"
}
```

### 说明

- 调用方读取此文件进行版本比对
- 当协议结构变更时，需更新 `version` 字段
- 当前版本为 `2.0.0`，表示协议冻结状态

---

## 附录 D：测试代码样例

### D.1 模型单元测试

**文件**：`tests/unittests/models/test_fake_image_models.py`

```python
import pytest
from pydantic import ValidationError
from src.models.fake_image_models import (
    FakeImageMeta,
    FakeSmallImageBiz,
    FakeBigImageBiz,
    FakeSmallImage,
    FakeBigImage,
)
from src.models.fake_result_models import FakeEvaluation


class TestFakeImageMeta:
    """FakeImageMeta 单元测试。"""

    def test_valid_meta(self):
        """合法输入。"""
        meta = FakeImageMeta(width=512, height=512, channel=3)
        assert meta.width == 512
        assert meta.height == 512
        assert meta.channel == 3

    def test_invalid_width_zero(self):
        """width = 0 非法。"""
        with pytest.raises(ValidationError) as exc_info:
            FakeImageMeta(width=0, height=512, channel=3)
        assert "must be positive" in str(exc_info.value)

    def test_invalid_width_negative(self):
        """width < 0 非法。"""
        with pytest.raises(ValidationError) as exc_info:
            FakeImageMeta(width=-1, height=512, channel=3)
        assert "must be positive" in str(exc_info.value)

    def test_invalid_height_zero(self):
        """height = 0 非法。"""
        with pytest.raises(ValidationError) as exc_info:
            FakeImageMeta(width=512, height=0, channel=3)
        assert "must be positive" in str(exc_info.value)

    def test_invalid_channel_zero(self):
        """channel = 0 非法。"""
        with pytest.raises(ValidationError) as exc_info:
            FakeImageMeta(width=512, height=512, channel=0)
        assert "must be positive" in str(exc_info.value)


class TestFakeSmallImageBiz:
    """FakeSmallImageBiz 单元测试。"""

    def test_valid_biz(self):
        """合法输入（必填字段）。"""
        biz = FakeSmallImageBiz(image_id="img-001")
        assert biz.image_id == "img-001"
        assert biz.position is None
        assert biz.camera_id is None

    def test_valid_biz_with_optional(self):
        """合法输入（含可选字段）。"""
        biz = FakeSmallImageBiz(
            image_id="img-001",
            position="left",
            camera_id="cam-01"
        )
        assert biz.position == "left"
        assert biz.camera_id == "cam-01"

    def test_invalid_image_id_empty(self):
        """image_id 为空字符串非法。"""
        with pytest.raises(ValidationError) as exc_info:
            FakeSmallImageBiz(image_id="")
        assert "image_id must not be empty" in str(exc_info.value)


class TestFakeSmallImage:
    """FakeSmallImage 单元测试。"""

    def test_valid_small_image(self):
        """合法输入。"""
        img = FakeSmallImage(
            image_base64="data:image/png;base64,AAA...",
            meta=FakeImageMeta(width=512, height=512, channel=3),
            biz=FakeSmallImageBiz(image_id="img-001"),
            evaluation=FakeEvaluation(features=[]),
        )
        assert img.image_base64 == "data:image/png;base64,AAA..."

    def test_invalid_image_base64_empty(self):
        """image_base64 为空非法。"""
        with pytest.raises(ValidationError) as exc_info:
            FakeSmallImage(
                image_base64="",
                meta=FakeImageMeta(width=512, height=512, channel=3),
                biz=FakeSmallImageBiz(image_id="img-001"),
                evaluation=FakeEvaluation(features=[]),
            )
        assert "image_base64 must not be empty" in str(exc_info.value)
```

---

### D.2 规则模型单元测试

**文件**：`tests/unittests/models/test_fake_rules_models.py`

```python
import pytest
from pydantic import ValidationError
from src.models.fake_rules_models import (
    FakeGroovesWidthMm,
    FakeRule6_1Config,
    FakeRule8Config,
    FakeRule6_1,
    FakeRule8,
)


class TestFakeRule6_1:
    """FakeRule6_1 单元测试。"""

    def test_valid_rule6_1(self):
        """合法输入。"""
        rule = FakeRule6_1(
            rule_name="rule6-1",
            description="图案连续性检测",
            score=10.0,
            rule_config=FakeRule6_1Config(gray_threshold_lte=200),
        )
        assert rule.rule_name == "rule6-1"
        assert rule.score == 10.0

    def test_invalid_rule_name(self):
        """rule_name 不等于 'rule6-1' 非法。"""
        with pytest.raises(ValidationError) as exc_info:
            FakeRule6_1(
                rule_name="wrong",
                description="图案连续性检测",
                score=10.0,
                rule_config=FakeRule6_1Config(gray_threshold_lte=200),
            )
        assert "rule_name must be 'rule6-1'" in str(exc_info.value)

    def test_invalid_score_negative(self):
        """score < 0 非法。"""
        with pytest.raises(ValidationError) as exc_info:
            FakeRule6_1(
                rule_name="rule6-1",
                description="图案连续性检测",
                score=-1.0,
                rule_config=FakeRule6_1Config(gray_threshold_lte=200),
            )
        assert "score must be non-negative" in str(exc_info.value)


class TestFakeRule8:
    """FakeRule8 单元测试。"""

    def test_valid_rule8(self):
        """合法输入。"""
        rule = FakeRule8(
            rule_name="rule8",
            description="横沟数量检测",
            score=4.0,
            rule_config=FakeRule8Config(
                grooves_width_mm=FakeGroovesWidthMm(center=3.5, side=1.8),
                grooves_lte=1,
            ),
        )
        assert rule.rule_name == "rule8"

    def test_invalid_rule_name(self):
        """rule_name 不等于 'rule8' 非法。"""
        with pytest.raises(ValidationError) as exc_info:
            FakeRule8(
                rule_name="wrong",
                description="横沟数量检测",
                score=4.0,
                rule_config=FakeRule8Config(
                    grooves_width_mm=FakeGroovesWidthMm(center=3.5, side=1.8),
                    grooves_lte=1,
                ),
            )
        assert "rule_name must be 'rule8'" in str(exc_info.value)
```

---

### D.3 API 集成测试

**文件**：`tests/integrations/test_fake_generation.py`

```python
import pytest
from src.api.fake_generation import generate_big_image_with_evaluation


def create_valid_input() -> dict:
    """构造合法输入数据（dict 格式）。"""
    return {
        "small_images": [
            {
                "image_base64": "data:image/png;base64,AAA...",
                "meta": {"width": 512, "height": 512, "channel": 3},
                "biz": {"image_id": "small-001", "position": "left"},
                "evaluation": {"features": []},
            },
            {
                "image_base64": "data:image/png;base64,BBB...",
                "meta": {"width": 512, "height": 512, "channel": 3},
                "biz": {"image_id": "small-002", "position": "right"},
                "evaluation": {"features": []},
            },
        ],
        "big_image": None,
        "rules_config": {
            "rule6_1": {
                "rule_name": "rule6-1",
                "description": "图案连续性检测",
                "score": 10,
                "rule_config": {"gray_threshold_lte": 200},
            },
            "rule8": {
                "rule_name": "rule8",
                "description": "横沟数量检测",
                "score": 4,
                "rule_config": {
                    "grooves_width_mm": {"center": 3.5, "side": 1.8},
                    "grooves_lte": 1,
                },
            },
        },
        "scheme_rank": 1,
        "is_debug": False,
        "flag": False,
        "err_code": None,
        "err_msg": None,
    }


class TestFakeGenerationAPI:
    """Fake Generation API 集成测试。"""

    def test_success_response(self):
        """成功输入返回成功响应。"""
        data = create_valid_input()
        result = generate_big_image_with_evaluation(data)

        assert result["flag"] is True
        assert result["err_code"] is None
        assert result["err_msg"] is None
        assert result["big_image"] is not None
        assert result["big_image"]["biz"]["status"] == "generated"

    def test_error_empty_small_images(self):
        """small_images 为空返回错误。"""
        data = create_valid_input()
        data["small_images"] = []
        result = generate_big_image_with_evaluation(data)

        assert result["flag"] is False
        assert result["err_code"] == "DATA_ERROR"
        assert "small_images must not be empty" in result["err_msg"]

    def test_error_big_image_not_none(self):
        """big_image 非空返回错误。"""
        data = create_valid_input()
        data["big_image"] = {"image_base64": "xxx"}
        result = generate_big_image_with_evaluation(data)

        assert result["flag"] is False
        assert result["err_code"] == "DATA_ERROR"
        assert "big_image must be None in request" in result["err_msg"]

    def test_error_is_debug_true(self):
        """is_debug=True 返回错误。"""
        data = create_valid_input()
        data["is_debug"] = True
        result = generate_big_image_with_evaluation(data)

        assert result["flag"] is False
        assert result["err_code"] == "DATA_ERROR"
        assert "is_debug must be False" in result["err_msg"]

    def test_error_flag_true(self):
        """flag=True 返回错误。"""
        data = create_valid_input()
        data["flag"] = True
        result = generate_big_image_with_evaluation(data)

        assert result["flag"] is False
        assert result["err_code"] == "DATA_ERROR"
        assert "flag must be False in request" in result["err_msg"]

    def test_error_rule6_1_wrong_name(self):
        """rule6_1.rule_name 错误返回错误。"""
        data = create_valid_input()
        data["rules_config"]["rule6_1"]["rule_name"] = "wrong"
        result = generate_big_image_with_evaluation(data)

        assert result["flag"] is False
        assert result["err_code"] == "DATA_ERROR"
        assert "rule_name must be 'rule6-1'" in result["err_msg"]
```

---

### D.4 运行测试

```bash
# 安装 pytest
pip install pytest

# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unittests/

# 运行集成测试
pytest tests/integrations/

# 查看覆盖率
pytest --cov=src tests/
```

---

**文档结束**
