# Fake Generation API 设计文档 v4

## 版本信息
- 文档版本：v4.0
- 创建日期：2026-04-29
- 状态：Draft
- 说明：本版本在 v3 基础上，进一步明确 fake 模型层错误收口方式，并补充缺失模型单元测试的具体落地改法。

---

## 一、任务目标

本次任务的目标是：

1. 补齐缺失的模型单元测试：
   - `tests/unittests/models/test_fake_result_models.py`
   - `tests/unittests/models/test_fake_tire_struct.py`
2. 明确 fake 模型层中“自行组织报错”的位置
3. 给出具体代码修改方案
4. 本文档作为执行文档，供 AI 或研发按文档直接落地

---

## 二、改动范围

仅允许关注以下文件：

### 2.1 允许修改的模型文件
- `src/models/fake_image_models.py`
- `src/models/fake_result_models.py`
- `src/models/fake_rules_models.py`
- `src/models/fake_tire_struct.py`

### 2.2 允许新增的测试文件
- `tests/unittests/models/test_fake_result_models.py`
- `tests/unittests/models/test_fake_tire_struct.py`

### 2.3 当前不动
- `src/api/fake_generation.py`
- 非 fake 前缀文件
- `version.json`

---

## 三、现状问题清单

### 3.1 `src/models/fake_image_models.py`
当前直接使用 `ValueError("...")`：

- `FakeImageMeta.validate_positive`
- `FakeSmallImageBiz.validate_image_id`
- `FakeBigImageBiz.validate_image_id`
- `FakeBaseImage.validate_image_base64`

### 3.2 `src/models/fake_result_models.py`
当前直接使用 `ValueError("...")`：

- `FakeFeatureResult.validate_rule_name`
- `FakeScoreResult.validate_rule_name`
- `FakeScoreResult.validate_score_range`

### 3.3 `src/models/fake_rules_models.py`
当前直接使用 `ValueError("...")`：

- `FakeGroovesWidthMm.validate_positive`
- `FakeRule8Config.validate_grooves_lte`
- `FakeRuleConfigBase.validate_score`
- `FakeRule6_1.validate_rule_name`
- `FakeRule8.validate_rule_name`

### 3.4 `src/models/fake_tire_struct.py`
当前虽然已经引入 `InputDataError`，但构建时仍然是：

```python
raise ValueError(str(error))
```

---

## 四、具体改法

### 4.1 修改 `src/models/fake_image_models.py`

#### 4.1.1 修改目标
把直接抛出的 `ValueError("...")` 改成统一先构造 `InputDataError`，再 `raise ValueError(str(error))`。

#### 4.1.2 需要新增 import
在文件顶部新增：

```python
from ..common.exceptions import InputDataError
```

#### 4.1.3 具体修改点

##### 1）`FakeImageMeta.validate_positive`

当前逻辑：

```python
if v <= 0:
    raise ValueError("must be positive")
```

改为：

```python
if v <= 0:
    error = InputDataError(
        object_name="FakeImageMeta",
        field_path=info.field_name,
        rule="must be positive",
        actual_value=v,
    )
    raise ValueError(str(error))
```

同时把函数签名从：

```python
def validate_positive(cls, v: int) -> int:
```

改为：

```python
def validate_positive(cls, v: int, info) -> int:
```

##### 2）`FakeSmallImageBiz.validate_image_id`

当前：

```python
if not v:
    raise ValueError("image_id must not be empty")
```

改为：

```python
if not v:
    error = InputDataError(
        object_name="FakeSmallImageBiz",
        field_path="image_id",
        rule="must not be empty",
        actual_value=v,
    )
    raise ValueError(str(error))
```

##### 3）`FakeBigImageBiz.validate_image_id`

当前：

```python
if not v:
    raise ValueError("image_id must not be empty")
```

改为：

```python
if not v:
    error = InputDataError(
        object_name="FakeBigImageBiz",
        field_path="image_id",
        rule="must not be empty",
        actual_value=v,
    )
    raise ValueError(str(error))
```

##### 4）`FakeBaseImage.validate_image_base64`

当前：

```python
if not v:
    raise ValueError("image_base64 must not be empty")
```

改为：

```python
if not v:
    error = InputDataError(
        object_name="FakeBaseImage",
        field_path="image_base64",
        rule="must not be empty",
        actual_value=v,
    )
    raise ValueError(str(error))
```

---

### 4.2 修改 `src/models/fake_result_models.py`

#### 4.2.1 修改目标
把直接抛出的 `ValueError("...")` 改成先构造 `InputDataError`，再 `raise ValueError(str(error))`。

#### 4.2.2 需要新增 import
新增：

```python
from ..common.exceptions import InputDataError
```

#### 4.2.3 具体修改点

##### 1）`FakeFeatureResult.validate_rule_name`

当前：

```python
if v not in ("rule6-1", "rule8"):
    raise ValueError("rule_name must be 'rule6-1' or 'rule8'")
```

改为：

```python
if v not in ("rule6-1", "rule8"):
    error = InputDataError(
        object_name="FakeFeatureResult",
        field_path="rule_name",
        rule="must be 'rule6-1' or 'rule8'",
        actual_value=v,
    )
    raise ValueError(str(error))
```

##### 2）`FakeScoreResult.validate_rule_name`

当前：

```python
if v not in ("rule6-1", "rule8"):
    raise ValueError("rule_name must be 'rule6-1' or 'rule8'")
```

改为：

```python
if v not in ("rule6-1", "rule8"):
    error = InputDataError(
        object_name="FakeScoreResult",
        field_path="rule_name",
        rule="must be 'rule6-1' or 'rule8'",
        actual_value=v,
    )
    raise ValueError(str(error))
```

##### 3）`FakeScoreResult.validate_score_range`

当前：

```python
if self.score_value > self.score_max:
    raise ValueError("score_value must be less than or equal to score_max")
```

改为：

```python
if self.score_value > self.score_max:
    error = InputDataError(
        object_name="FakeScoreResult",
        field_path="score_value",
        rule="must be less than or equal to score_max",
        actual_value=self.score_value,
    )
    raise ValueError(str(error))
```

---

### 4.3 修改 `src/models/fake_rules_models.py`

#### 4.3.1 修改目标
把直接抛出的 `ValueError("...")` 改成先构造 `InputDataError`，再 `raise ValueError(str(error))`。

#### 4.3.2 需要新增 import
新增：

```python
from ..common.exceptions import InputDataError
```

#### 4.3.3 具体修改点

##### 1）`FakeGroovesWidthMm.validate_positive`

当前：

```python
if v <= 0:
    raise ValueError("must be positive")
```

改为：

```python
if v <= 0:
    error = InputDataError(
        object_name="FakeGroovesWidthMm",
        field_path=info.field_name,
        rule="must be positive",
        actual_value=v,
    )
    raise ValueError(str(error))
```

同时把函数签名从：

```python
def validate_positive(cls, v: float) -> float:
```

改为：

```python
def validate_positive(cls, v: float, info) -> float:
```

##### 2）`FakeRule8Config.validate_grooves_lte`

当前：

```python
if v < 0:
    raise ValueError("must be non-negative")
```

改为：

```python
if v < 0:
    error = InputDataError(
        object_name="FakeRule8Config",
        field_path="grooves_lte",
        rule="must be non-negative",
        actual_value=v,
    )
    raise ValueError(str(error))
```

##### 3）`FakeRuleConfigBase.validate_score`

当前：

```python
if v < 0:
    raise ValueError("score must be non-negative")
```

改为：

```python
if v < 0:
    error = InputDataError(
        object_name="FakeRuleConfigBase",
        field_path="score",
        rule="must be non-negative",
        actual_value=v,
    )
    raise ValueError(str(error))
```

##### 4）`FakeRule6_1.validate_rule_name`

当前：

```python
if self.rule_name != "rule6-1":
    raise ValueError("rule_name must be 'rule6-1'")
```

改为：

```python
if self.rule_name != "rule6-1":
    error = InputDataError(
        object_name="FakeRule6_1",
        field_path="rule_name",
        rule="must be 'rule6-1'",
        actual_value=self.rule_name,
    )
    raise ValueError(str(error))
```

##### 5）`FakeRule8.validate_rule_name`

当前：

```python
if self.rule_name != "rule8":
    raise ValueError("rule_name must be 'rule8'")
```

改为：

```python
if self.rule_name != "rule8":
    error = InputDataError(
        object_name="FakeRule8",
        field_path="rule_name",
        rule="must be 'rule8'",
        actual_value=self.rule_name,
    )
    raise ValueError(str(error))
```

---

### 4.4 修改 `src/models/fake_tire_struct.py`

#### 4.4.1 修改目标
保持现有 `_get_request_validation_error()` 逻辑不变，仅保持它继续产出 `InputDataError`。
构建时仍走 Pydantic 兼容路径，但单元测试要显式覆盖这一行为。

#### 4.4.2 代码层面本轮可不改逻辑
当前：

```python
@model_validator(mode="after")
def validate_request_on_build(self) -> "FakeTireStruct":
    error = self._get_request_validation_error()
    if error is not None:
        raise ValueError(str(error))
    return self
```

这个逻辑本轮可以保留，不强制再改。

#### 4.4.3 本轮重点
重点是给它补独立单元测试，明确覆盖：
- 自动校验报错
- `validate_request()` 返回字符串
- 合法请求返回 `None`

---

## 五、新增测试文件的具体写法

### 5.1 新增 `tests/unittests/models/test_fake_result_models.py`

测试文件中应包含以下测试类和测试点。

#### 5.1.1 导入
```python
import pytest
from pydantic import ValidationError

from src.models.fake_result_models import (
    FakeEvaluation,
    FakeFeatureResult,
    FakeLineage,
    FakeScoreResult,
)
```

#### 5.1.2 测试点

##### `TestFakeFeatureResult`
1. `test_valid_feature_result`
2. `test_invalid_rule_name`

##### `TestFakeEvaluation`
3. `test_valid_empty_features`
4. `test_valid_features`

##### `TestFakeScoreResult`
5. `test_valid_score_result`
6. `test_invalid_rule_name`
7. `test_invalid_score_value_gt_score_max`

##### `TestFakeLineage`
8. `test_valid_lineage`

#### 5.1.3 错误断言要求
错误信息断言要改为新的定位型字符串，例如：

- `FakeFeatureResult.rule_name: must be 'rule6-1' or 'rule8', got 'wrong'`
- `FakeScoreResult.score_value: must be less than or equal to score_max, got 5.0`

---

### 5.2 新增 `tests/unittests/models/test_fake_tire_struct.py`

#### 5.2.1 导入
```python
import pytest
from pydantic import ValidationError

from src.models.fake_tire_struct import FakeTireStruct
```

#### 5.2.2 文件内先定义一个合法输入 helper

```python
def create_valid_input() -> dict:
    return {
        "small_images": [
            {
                "image_base64": "data:image/png;base64,AAA...",
                "meta": {"width": 512, "height": 512, "channel": 3},
                "biz": {"image_id": "small-001", "position": "left", "camera_id": "cam-01"},
                "evaluation": {"features": []},
            }
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
```

#### 5.2.3 测试类与测试点

##### `TestFakeTireStruct`
1. `test_valid_model_validate`
2. `test_validate_request_returns_none_when_valid`
3. `test_invalid_empty_small_images`
4. `test_invalid_big_image_not_none`
5. `test_invalid_scheme_rank`
6. `test_invalid_is_debug_true`
7. `test_invalid_flag_true`
8. `test_invalid_err_code_not_none`
9. `test_invalid_err_msg_not_none`
10. `test_validate_request_returns_error_message_for_constructed_invalid_instance`

#### 5.2.4 特别说明
第 10 个测试必须使用：

```python
FakeTireStruct.model_construct(...)
```

来绕过自动校验，然后验证：

```python
validate_request()
```

返回错误字符串，而不是抛异常。

#### 5.2.5 错误断言要求
例如：

- `FakeTireStruct.small_images: must not be empty, got []`
- `FakeTireStruct.big_image: must be None in request`
- `FakeTireStruct.scheme_rank: must be >= 1, got 0`
- `FakeTireStruct.flag: must be False in request, got True`

---

## 六、执行顺序

后续 AI 真正执行时，按下面顺序：

1. 修改 `src/models/fake_image_models.py`
2. 修改 `src/models/fake_result_models.py`
3. 修改 `src/models/fake_rules_models.py`
4. `src/models/fake_tire_struct.py` 保持现有逻辑，仅复核是否无需调整
5. 新增 `tests/unittests/models/test_fake_result_models.py`
6. 新增 `tests/unittests/models/test_fake_tire_struct.py`
7. 运行以下测试：
   - `tests/unittests/models/test_fake_image_models.py`
   - `tests/unittests/models/test_fake_result_models.py`
   - `tests/unittests/models/test_fake_rules_models.py`
   - `tests/unittests/models/test_fake_tire_struct.py`
   - `tests/integrations/test_fake_generation.py`

---

## 七、执行结果要求

执行完成后应满足：

1. fake 模型层新增错误信息统一走 `InputDataError -> str(error) -> ValueError(...)` 路径
2. `fake_result_models.py` 有独立单元测试
3. `fake_tire_struct.py` 有独立单元测试
4. 原有集成测试仍通过
5. 不修改 `src/api/fake_generation.py`
6. 不修改非 fake 前缀文件
7. 不修改 `version.json`

---

## 八、与上位文档的关系

执行本文件时，仍需同时遵守：
- `docs/ai_context_entrypoint.md`
- `docs/project_coding_standards.md`
- `docs/project_coding_standards_agent.md`
- `docs/exception_handling_design.md`

当本文件与旧版 `FakeGenerationAPI_v2.md`、`FakeGenerationAPI_v3.md` 冲突时，以本文件为准。

---

**文档结束**
