# Fake Generation API 设计文档 v2

## 版本信息
- 文档版本：v2.0
- 创建日期：2026-04-29
- 状态：Draft
- 说明：本版本替代原文档中的 `dict -> dict` 主入口设计，改为实例输入、实例输出设计。

---

## 一、设计目标

### 1.1 核心目标
本次设计目标是实现一个 **fake API**，用于验证调用方是否能按期望结构发送输入数据，并验证调用方是否能正确构造 `FakeTireStruct` 实例。

### 1.2 具体目标
1. 冻结 `generation` 接口的输入输出协议
2. 验证两层嵌套数据结构的合理性
3. 测试调用方能否正确构造 `FakeTireStruct` 输入对象
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

### 2.3 主入口实例化输入
- API 主入口直接接收 `FakeTireStruct` 实例
- API 主入口不负责从原始 `dict` 构造输入对象
- 调用方负责先实例化 `FakeTireStruct`

### 2.4 双重校验机制
- `FakeTireStruct` 构建时自动检查
- API 主入口拿到实例后，仍需再次显式调用实例的请求态检查方法

### 2.5 薄层 API 设计
- API 层只负责调用模型校验和构造响应
- 校验逻辑在模型层实现

---

## 三、文件结构

### 3.1 文件清单

```
version.json                           # 项目版本文件
src/
├── api/
│   └── fake_generation.py            # fake API 入口
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
| `fake_generation.py` | API 入口，输入实例检查，响应构造 |
| `fake_tire_struct.py` | API 顶层输入输出对象 |
| `fake_image_models.py` | 所有图像相关模型 |
| `fake_rules_models.py` | 所有规则配置相关模型 |
| `fake_result_models.py` | 所有输出结果相关模型 |
| `test_fake_generation.py` | API 集成测试 |

---

## 四、数据模型设计

### 4.1 技术选型

使用 **pydantic v2** 作为数据模型框架。

### 4.2 顶层模型要求

`FakeTireStruct` 应同时支持两种检查方式：

1. **构建时自动检查**
   - 在 `model_validate(...)` 或实例化时自动执行请求态检查
2. **实例级显式检查**
   - 实例提供 `validate_request()` 方法
   - 供 API 主入口或其他上层代码主动调用

### 4.3 显式检查方法约束

- `validate_request()` 不接收额外输入参数
- `validate_request()` 基于实例自身状态检查
- `validate_request()` 返回 `str | None`
  - 成功：返回 `None`
  - 失败：返回错误信息字符串

### 4.4 校验逻辑复用要求

- 构建时自动检查与实例级显式检查必须复用同一套底层校验逻辑
- 不允许维护两套独立请求态校验规则

---

## 五、Pydantic 使用说明

### 5.1 安装依赖

```bash
pip install pydantic
```

### 5.2 输入对象实例化

调用方应先从原始 `dict` 构造 `FakeTireStruct` 实例。推荐统一使用：

```python
FakeTireStruct.model_validate(data)
```

不推荐在项目内为此额外封装自定义 helper（例如 `build_tire_struct(data)`），除非后续确有跨模块统一装载需求。

### 5.3 测试输入组织方式

测试中应：
1. 先用 `dict` 写输入，保证可读性
2. 再在测试中统一使用 `FakeTireStruct.model_validate(data)` 构造实例
3. 把实例传给主函数
4. 对返回实例使用 `model_dump()` 后与预期 `dict` 比较

---

## 六、API 设计

### 6.1 主函数签名

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

### 6.2 主函数职责

主函数必须做以下检查：

1. **类型检查**
   - 检查入参是否为 `FakeTireStruct`
   - 如果不是，抛出 `TypeError`

2. **实例级请求态检查**
   - 显式调用 `tire_struct.validate_request()`
   - 如果失败，返回失败响应对象

3. **成功响应构造**
   - 如果检查通过，返回成功响应对象

### 6.3 类型错误与业务错误的区分

- 参数类型错误、调用方式错误：视为编程错误，抛异常
- 请求态字段非法：视为业务输入错误，返回失败响应对象

### 6.4 辅助函数

#### create_error_response

```python
def create_error_response(original: FakeTireStruct, err_msg: str) -> FakeTireStruct:
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

## 七、错误码设计

| 错误码 | 类别 | 说明 |
|--------|------|------|
| `DATA_ERROR` | 数据错误 | 输入数据校验失败（缺少字段、类型错误、值范围错误等） |
| `RUNTIME_ERROR` | 运行时错误 | 代码执行出错（内部异常） |

---

## 八、输入输出样例

### 8.1 成功输入样例

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
```

### 8.2 成功调用样例

```python
result = generate_big_image_with_evaluation(tire_struct)
```

### 8.3 成功输出样例

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

---

## 九、测试策略

### 9.1 集成测试规范

集成测试应遵循以下规则：

- 输入先使用 `dict` 定义，便于人类阅读
- 测试中统一用 `FakeTireStruct.model_validate(data)` 构造实例
- 主函数调用时传入 `FakeTireStruct` 实例
- 返回结果统一使用 `result.model_dump()` 后与预期 `dict` 比较

### 9.2 测试组织建议

推荐测试中使用：
- `create_valid_input() -> dict`
- `expected_success_output() -> dict`（如需要）
- 在测试体内调用 `FakeTireStruct.model_validate(data)`

不推荐：
- 自定义 `build_tire_struct(data)` 之类的薄包装 helper

---

## 十、与全局规范的关系

本设计文档执行时，仍需遵守：
- `docs/project_coding_standards.md`
- `docs/project_coding_standards_agent.md`

其中尤其适用的规则包括：
- API 层保持薄层
- 数据模型负责结构校验
- 每个函数应对自己的入参边界负责
- 测试优先明确输入与预期输出

---

## 十一、总结

### 11.1 本版本的核心变化

相对于旧版设计，本版本明确改为：

1. API 主入口接收 `FakeTireStruct` 实例，而非原始 `dict`
2. `FakeTireStruct` 同时支持构建时自动检查与实例级显式检查
3. API 主函数必须显式再次调用实例检查方法
4. 测试中统一采用 `dict -> model_validate -> 实例 -> 主函数 -> model_dump()` 的工程化路径

### 11.2 协作建议

- 旧版文档保留，仅作为历史参考
- 新实现、新测试、新评审应统一参考本 v2 文档
- 后续 AI/人类协作时，优先引用 `FakeGenerationAPI_v2.md`

---

**文档结束**
