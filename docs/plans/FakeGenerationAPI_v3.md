# Fake Generation API 设计文档 v3

## 版本信息
- 文档版本：v3.0
- 创建日期：2026-04-29
- 状态：Draft
- 说明：本版本在 v2 基础上进一步明确主入口实例边界、双重校验机制、异常管理接入方式与测试实例化策略。

---

## 一、设计目标

### 1.1 核心目标
本次设计目标是实现一个 **fake API**，用于验证调用方是否能按期望结构发送输入数据，并验证调用方是否能正确构造 `FakeTireStruct` 实例。

### 1.2 具体目标
1. 冻结 `generation` 接口的输入输出协议
2. 验证两层嵌套数据结构的合理性
3. 测试调用方能否正确构造 `FakeTireStruct` 输入对象
4. 降低后续交互设计风险
5. 明确异常分类、边界校验与错误映射策略

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

### 2.3 主入口实例化输入
- API 主入口直接接收 `FakeTireStruct` 实例
- API 主入口不负责从原始 `dict` 构造输入对象
- 调用方负责先实例化 `FakeTireStruct`

### 2.4 双重校验机制
- `FakeTireStruct` 构建时自动检查
- API 主入口拿到实例后，仍需再次显式调用实例的请求态检查方法

### 2.5 函数边界负责制
- 每个函数应对自己的入参边界负责
- 主入口必须主动检查入参类型是否满足约定
- 主入口不得盲信调用方传入的实例状态

### 2.6 异常管理集中化
- 异常分类应集中定义
- 数据模型层负责检查，不负责错误协议
- API 边界层负责统一错误映射
- 不允许在多个文件中散落实现同类错误映射规则

### 2.7 薄层 API 设计
- API 层只负责调用模型校验和构造响应
- 校验逻辑在模型层实现
- 错误码与错误对象构造在边界层统一管理

---

## 三、文件结构

### 3.1 文件清单

```
version.json                           # 项目版本文件
src/
├── api/
│   └── fake_generation.py            # fake API 入口
│
├── common/
│   └── exceptions.py                 # 项目统一异常定义
│
└── models/
    ├── fake_tire_struct.py           # 顶层聚合对象
    ├── fake_image_models.py          # 图像相关模型
    ├── fake_rules_models.py          # 规则相关模型
    └── fake_result_models.py         # 结果相关模型

tests/
├── integrations/
│   └── test_fake_generation.py       # fake API 集成测试
└── unittests/
    └── models/
        ├── test_fake_image_models.py
        └── test_fake_rules_models.py
```

### 3.2 文件职责

| 文件 | 职责 |
|------|------|
| `version.json` | 项目版本信息，调用方读取进行版本比对 |
| `src/common/exceptions.py` | 项目统一异常分类与异常信息结构 |
| `fake_generation.py` | API 入口，输入实例检查，错误映射，响应构造 |
| `fake_tire_struct.py` | API 顶层输入输出对象 |
| `fake_image_models.py` | 所有图像相关模型 |
| `fake_rules_models.py` | 所有规则相关模型 |
| `fake_result_models.py` | 所有输出结果相关模型 |
| `test_fake_generation.py` | API 集成测试 |

---

## 四、异常管理设计

### 4.1 异常分类

推荐采用项目统一异常体系：

```python
ProjectError
├── InputError
│   ├── InputTypeError
│   └── InputDataError
└── RuntimeProcessError
```

### 4.2 各类异常职责

#### InputTypeError
用于表示：
- 函数收到的参数类型不符合约定

示例：
- `generate_big_image_with_evaluation` 期望收到 `FakeTireStruct`
- 实际收到 `dict`

这类错误属于：
- 编程错误
- 调用方式错误

处理方式：
- 直接抛出
- 不映射为业务失败响应对象

#### InputDataError
用于表示：
- 参数类型正确
- 但数据内容不满足约束

示例：
- `big_image must be None in request`
- `scheme_rank must be >= 1`

处理方式：
- 在边界层映射为 `DATA_ERROR`

#### RuntimeProcessError
用于表示：
- 执行过程失败
- 问题不在输入本身

示例：
- 构造成功响应对象时发生内部异常

处理方式：
- 在边界层映射为 `RUNTIME_ERROR`

### 4.3 异常信息要求

异常信息必须具有定位价值。

#### InputTypeError 必须包含
- 函数名
- 参数名
- 期望类型
- 实际类型

示例：

```text
generate_big_image_with_evaluation: argument 'tire_struct' expects FakeTireStruct, got dict
```

#### InputDataError 必须包含
- 对象名
- 字段路径
- 违反的规则
- 必要时给出实际值

示例：

```text
FakeTireStruct.scheme_rank: must be >= 1, got 0
```

#### RuntimeProcessError 必须包含
- 执行阶段或函数名
- 高层失败说明
- 原始异常信息

示例：

```text
create_success_response: failed to build fake big image: 'NoneType' object has no attribute 'rule6_1'
```

---

## 五、数据模型设计

### 5.1 技术选型

使用 **pydantic v2** 作为数据模型框架。

### 5.2 顶层模型要求

`FakeTireStruct` 必须同时支持两种检查方式：

1. **构建时自动检查**
   - 在 `model_validate(...)` 或实例化时自动执行请求态检查
2. **实例级显式检查**
   - 实例提供 `validate_request()` 方法
   - 供 API 主入口或其他上层代码主动调用

### 5.3 显式检查方法约束

- `validate_request()` 不接收额外输入参数
- `validate_request()` 基于实例自身状态检查
- `validate_request()` 返回 `str | None`
  - 成功：返回 `None`
  - 失败：返回错误信息字符串

### 5.4 校验逻辑复用要求

- 构建时自动检查与实例级显式检查必须复用同一套底层校验逻辑
- 不允许维护两套独立请求态校验规则

### 5.5 异常接入要求

- 底层共享校验逻辑应优先生成 `InputDataError` 风格的定位信息
- 构建时自动检查可转为 Pydantic 兼容异常
- 实例级显式检查应返回可直接用于错误响应的错误字符串

---

## 六、Pydantic 使用说明

### 6.1 安装依赖

```bash
pip install pydantic
```

### 6.2 输入对象实例化

调用方应先从原始 `dict` 构造 `FakeTireStruct` 实例。推荐统一使用：

```python
FakeTireStruct.model_validate(data)
```

不推荐在项目内为此额外封装自定义 helper（例如 `build_tire_struct(data)`），除非后续确有跨模块统一装载需求。

### 6.3 测试输入组织方式

测试中应：
1. 先用 `dict` 写输入，保证可读性
2. 再在测试中统一使用 `FakeTireStruct.model_validate(data)` 构造实例
3. 把实例传给主函数
4. 对返回实例使用 `model_dump()` 后与预期 `dict` 比较

---

## 七、API 设计

### 7.1 主函数签名

```python
def generate_big_image_with_evaluation(tire_struct: FakeTireStruct) -> FakeTireStruct:
    """
    Fake API: 根据小图生成大图并返回评分结果。

    本函数仅用于验证输入输出协议，不实现真实流程。

    Args:
        tire_struct: 已成功实例化的 FakeTireStruct 输入对象

    Returns:
        FakeTireStruct: 成功或失败响应对象
    """
```

### 7.2 主函数职责

主函数必须做以下检查：

1. **类型检查**
   - 检查入参是否为 `FakeTireStruct`
   - 如果不是，抛出 `InputTypeError`

2. **实例级请求态检查**
   - 显式调用 `tire_struct.validate_request()`
   - 如果失败，返回失败响应对象

3. **成功响应构造**
   - 如果检查通过，返回成功响应对象

4. **运行时异常映射**
   - 如果成功路径内部发生运行时异常，统一映射为 `RUNTIME_ERROR`

### 7.3 类型错误与业务错误的区分

- 参数类型错误、调用方式错误：视为编程错误，抛异常
- 请求态字段非法：视为业务输入错误，返回失败响应对象
- 内部执行异常：视为运行时错误，返回失败响应对象

### 7.4 辅助函数

#### create_error_response

```python
def create_error_response(original: FakeTireStruct, err_code: str, err_msg: str) -> FakeTireStruct:
    """构造失败响应对象。"""
```

说明：
- 使用已实例化的 `FakeTireStruct` 作为原始输入来源
- 返回 `FakeTireStruct` 失败响应对象

#### create_success_response

```python
def create_success_response(original: FakeTireStruct) -> FakeTireStruct:
    """构造成功响应对象（fake 固定输出）。"""
```

说明：
- 使用已实例化的 `FakeTireStruct` 作为原始输入来源
- 返回 `FakeTireStruct` 成功响应对象

---

## 八、错误码设计

| 错误码 | 类别 | 说明 |
|--------|------|------|
| `DATA_ERROR` | 数据错误 | 输入数据校验失败 |
| `RUNTIME_ERROR` | 运行时错误 | 代码执行出错（内部异常） |

---

## 九、输入输出样例

### 9.1 成功输入样例

```python
data = {
    "small_images": [
        {
            "image_base64": "data:image/png;base64,AAA...",
            "meta": {"width": 512, "height": 512, "channel": 3},
            "biz": {"image_id": "small-001", "position": "left", "camera_id": "cam-01"},
            "evaluation": {"features": []},
        },
        {
            "image_base64": "data:image/png;base64,BBB...",
            "meta": {"width": 512, "height": 512, "channel": 3},
            "biz": {"image_id": "small-002", "position": "right", "camera_id": "cam-01"},
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

tire_struct = FakeTireStruct.model_validate(data)
result = generate_big_image_with_evaluation(tire_struct)
```

### 9.2 成功输出样例

```python
result.model_dump() == {
    "small_images": [...],
    "big_image": {
        "image_base64": "data:image/png;base64,FAKE_BIG_IMAGE_PLACEHOLDER",
        "meta": {"width": 1024, "height": 512, "channel": 3},
        "biz": {"image_id": "big-001", "scheme_rank": 1, "status": "generated"},
        "evaluation": {
            "features": [
                {
                    "rule_name": "rule6-1",
                    "feature_name": "pattern_continuity",
                    "feature_value": "good",
                    "description": "图案连续性",
                },
                {
                    "rule_name": "rule8",
                    "feature_name": "groove_count",
                    "feature_value": "1",
                    "description": "横沟数量",
                },
            ]
        },
        "scores": [
            {
                "rule_name": "rule6-1",
                "description": "图案连续性检测",
                "score_value": 8.0,
                "score_max": 10.0,
                "reason": "连续性基本满足要求",
            },
            {
                "rule_name": "rule8",
                "description": "横沟数量检测",
                "score_value": 4.0,
                "score_max": 4.0,
                "reason": "横沟数量满足要求",
            },
        ],
        "lineage": {
            "source_image_ids": ["small-001", "small-002"],
            "scheme_rank": 1,
            "summary": "由 2 张小图按第 1 名方案生成大图",
        },
    },
    "rules_config": {...},
    "scheme_rank": 1,
    "is_debug": False,
    "flag": True,
    "err_code": None,
    "err_msg": None,
}
```

### 9.3 类型错误样例

```python
generate_big_image_with_evaluation({})
```

预期：
- 抛出 `InputTypeError`
- 不返回业务失败响应对象

---

## 十、测试策略

### 10.1 集成测试规范

集成测试应遵循以下规则：

- 输入先使用 `dict` 定义，便于人类阅读
- 测试中统一用 `FakeTireStruct.model_validate(data)` 构造实例
- 主函数调用时传入 `FakeTireStruct` 实例
- 返回结果统一使用 `result.model_dump()` 后与预期 `dict` 比较

### 10.2 测试组织建议

推荐测试中使用：
- `create_valid_input() -> dict`
- `expected_success_output() -> dict`（如需要）
- 在测试体内调用 `FakeTireStruct.model_validate(data)`

不推荐：
- 自定义 `build_tire_struct(data)` 之类的薄包装 helper

### 10.3 错误场景测试建议

- 类型错误测试：断言抛出 `InputTypeError`
- 数据错误测试：断言返回 `DATA_ERROR` 响应对象
- 运行时错误测试：断言返回 `RUNTIME_ERROR` 响应对象（如有对应场景）

---

## 十一、需修改文件清单

### 必改文件
- `src/common/exceptions.py`
- `src/models/fake_tire_struct.py`
- `src/api/fake_generation.py`
- `tests/integrations/test_fake_generation.py`

### 暂不修改文件
- `src/models/fake_image_models.py`
- `src/models/fake_rules_models.py`
- `src/models/fake_result_models.py`
- `tests/unittests/models/test_fake_image_models.py`
- `tests/unittests/models/test_fake_rules_models.py`

前提：
- 不调整这些模型的字段与基础行为
- 仅调整顶层请求校验机制、主入口边界和集成测试调用方式

---

## 十二、推荐实施顺序

1. 先引入 `src/common/exceptions.py`
2. 再改 `src/models/fake_tire_struct.py`
3. 再改 `src/api/fake_generation.py`
4. 再改 `tests/integrations/test_fake_generation.py`
5. 最后运行测试并核对文档一致性

---

## 十三、与全局规范的关系

本设计文档执行时，仍需遵守：
- `docs/ai_context_entrypoint.md`
- `docs/project_coding_standards.md`
- `docs/project_coding_standards_agent.md`
- `docs/exception_handling_design.md`

其中尤其适用的规则包括：
- API 层保持薄层
- 数据模型负责结构校验
- 每个函数应对自己的入参边界负责
- 测试优先明确输入与预期输出
- 异常分类应集中定义

---

## 十四、总结

### 14.1 本版本的核心变化

相对于 v2，本版本进一步明确：

1. API 主入口接收 `FakeTireStruct` 实例，而非原始 `dict`
2. `FakeTireStruct` 同时支持构建时自动检查与实例级显式检查
3. API 主函数必须显式再次调用实例检查方法
4. 异常分类采用统一设计：`InputTypeError` / `InputDataError` / `RuntimeProcessError`
5. 测试中统一采用 `dict -> model_validate -> 实例 -> API -> model_dump()` 的工程化路径

### 14.2 协作建议

- 旧版本文档保留，仅作为历史参考
- 新实现、新测试、新评审应统一参考本 v3 文档
- 后续 AI/人类协作时，优先引用 `FakeGenerationAPI_v3.md`

---

**文档结束**
