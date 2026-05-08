# 通用异常类测试方案

## 1. 目标

为项目通用异常类 (`src/common/exceptions.py`) 提供完整的测试覆盖，验证：
- 异常继承体系正确
- 所有异常类的字段和消息格式符合规范
- RuntimeProcessError 能正确包装真实 Python 执行错误
- 各层异常处理职责分离正确
- 异常消息具有可定位性，不吞掉底层上下文

## 2. 测试文件位置

`tests/unittests/common/test_exceptions.py`

## 3. 导入规范

```python
from src.common.exceptions import (
    ProjectError,
    InputError,
    InputTypeError,
    InputDataError,
    RuntimeProcessError,
)
```

## 4. 测试数据

```python
SAMPLE_PYTHON_ERRORS = [
    ValueError("invalid value"),
    TypeError("'NoneType' object has no attribute 'process'"),
    KeyError("'missing_key'"),
    IndexError("list index out of range"),
    AttributeError("'dict' object has no attribute 'rule6_1'"),
    ZeroDivisionError("division by zero"),
    FileNotFoundError("[Errno 2] No such file or directory: '/path/to/file'"),
    RuntimeError("unexpected execution failure"),
]
```

## 5. 测试类清单

### 5.1 TestExceptionInheritance - 继承体系完整性
| 测试方法 | 验证点 |
|----------|--------|
| `test_input_type_error_chain` | InputTypeError → InputError → ProjectError → Exception → BaseException |
| `test_input_data_error_chain` | InputDataError → InputError → ProjectError → Exception |
| `test_runtime_process_error_chain` | RuntimeProcessError → ProjectError → Exception |
| `test_input_type_error_is_not_runtime_error` | InputTypeError 不是 RuntimeProcessError 子类 |
| `test_input_data_error_is_not_runtime_error` | InputDataError 不是 RuntimeProcessError 子类 |
| `test_catch_by_parent_type` | 所有异常可用 ProjectError 捕获 |
| `test_catch_input_errors_together` | InputTypeError/InputDataError 可用 InputError 捕获 |

### 5.2 TestInputTypeErrorFields - 字段完整性
| 测试方法 | 验证点 |
|----------|--------|
| `test_all_structured_fields` | function, param, expected_type, actual_type 正确赋值 |
| `test_inherited_fields_from_project_error` | message, location, details, cause 正确 |
| `test_details_dict_contains_all_fields` | details 包含所有必要字段 |
| `test_details_dict_values_match_attributes` | details 值与属性一致 |

### 5.3 TestInputTypeErrorMessageFormat - 消息格式
| 测试方法 | 验证点 |
|----------|--------|
| `test_standard_format` | `<function>: argument '<param>' expects <ExpectedType>, got <ActualType>` |
| `test_with_complex_type_names` | 复杂类型名称如 `List[FakeTireStruct]` |
| `test_with_class_name_actual_type` | 使用 `type().__name__` 获取实际类型 |

### 5.4 TestInputDataErrorFields - 字段完整性
| 测试方法 | 验证点 |
|----------|--------|
| `test_all_structured_fields` | object_name, field_path, rule, actual_value 正确赋值 |
| `test_inherited_fields` | location, details 正确 |

### 5.5 TestInputDataErrorMessageFormat - 消息格式覆盖
| 测试方法 | 验证点 |
|----------|--------|
| `test_with_actual_value` | 包含实际值：`Obj.field: rule, got 'value'` |
| `test_without_actual_value` | actual_value=None 时不包含 `got` |
| `test_with_none_explicit` | 显式传递 None |
| `test_with_integer_value` | 整数实际值 |
| `test_with_dict_value` | 字典实际值 |
| `test_with_list_value` | 列表实际值 |
| `test_with_long_string_value` | 长字符串实际值 |
| `test_with_special_characters` | 特殊字符 |
| `test_with_unicode` | Unicode 字符 |

### 5.6 TestInputDataErrorRealWorldScenarios - 真实场景
| 测试方法 | 验证点 |
|----------|--------|
| `test_scheme_rank_invalid` | FakeTireStruct.scheme_rank 非法 |
| `test_small_images_empty` | FakeTireStruct.small_images 为空 |
| `test_big_image_not_none` | FakeTireStruct.big_image 请求中非 None |
| `test_nested_field_path` | 嵌套字段路径 `big_image.meta.width` |

### 5.7 TestRuntimeProcessErrorFields - 字段完整性
| 测试方法 | 验证点 |
|----------|--------|
| `test_all_structured_fields` | stage, original_error 正确赋值 |
| `test_inherited_fields` | location, details, cause 正确 |
| `test_exception_chain_is_preserved` | `__cause__` 链被保留 |

### 5.8 TestRuntimeProcessErrorMessageFormat - 消息格式
| 测试方法 | 验证点 |
|----------|--------|
| `test_standard_format` | `<stage>: <high_level_failure>: <original_error>` |
| `test_message_contains_all_parts` | 消息包含所有部分 |

### 5.9 TestRuntimeProcessErrorRealPythonErrors - 包装真实 Python 错误
| 测试方法 | 验证点 |
|----------|--------|
| `test_wrap_various_python_errors` | 参数化测试 7 种 Python 异常类型 |
| `test_wrap_none_type_attribute_error` | None 属性访问 - 最常见场景 |
| `test_wrap_key_error_from_dict_access` | 字典键缺失 |
| `test_wrap_value_error_from_parsing` | 解析/转换错误 |
| `test_wrap_zero_division` | 除零错误 |
| `test_wrap_index_error` | 索引越界 |

### 5.10 TestRealExecutionScenarios - 真实执行场景
| 测试方法 | 验证点 |
|----------|--------|
| `test_method_raises_attribute_error_wrapped` | 调用 None 的属性触发 AttributeError 并包装 |
| `test_method_raises_key_error_wrapped` | 字典访问缺失键触发 KeyError 并包装 |
| `test_method_raises_type_error_wrapped` | 类型不匹配触发 TypeError 并包装 |
| `test_method_raises_value_error_wrapped` | JSON 解析失败触发 ValueError 并包装 |
| `test_chained_exception_preserves_full_context` | 内层函数抛出，外层包装，验证完整上下文 |
| `test_nested_wr_exception` | 多层包装（level3 → level2 → level1） |
| `test_runtime_error_used_in_api_pattern` | RuntimeProcessError 在 API 模式中的使用 |
| `test_original_error_traceback_accessible` | 原始异常的 `__traceback__` 可访问 |
| `test_error_can_be_re_raised` | 包装后的异常可以再次抛出 |

### 5.11 TestBoundaryConditions - 边界条件
| 测试方法 | 验证点 |
|----------|--------|
| `test_input_type_error_empty_strings` | 空字符串参数 |
| `test_input_data_error_empty_object_and_field` | 空对象名和字段 |
| `test_runtime_error_empty_stage_and_failure` | 空阶段和失败描述 |
| `test_input_data_error_with_empty_string_as_value` | 实际值为空字符串 |
| `test_input_data_error_with_false_as_value` | 实际值为 False |
| `test_input_data_error_with_zero_as_value` | 实际值为 0 |

### 5.12 TestExceptionHandlingIntegration - 分层集成
| 测试方法 | 验证点 |
|----------|--------|
| `test_api_layer_does_not_catch_type_error` | API 层不捕获 InputTypeError |
| `test_data_error_converted_to_data_error_response` | InputDataError → DATA_ERROR 响应 |
| `test_runtime_error_converted_to_runtime_error_response` | RuntimeProcessError → RUNTIME_ERROR 响应 |
| `test_full_api_pattern_with_all_three_error_types` | 完整 API 模式：三种错误类型 |
| `test_multiple_validations_first_error_returned` | 多个校验只返回第一个错误 |
| `test_error_response_preserves_original_context` | 错误响应保留原始上下文 |

### 5.13 TestExceptionSerialization - 序列化
| 测试方法 | 验证点 |
|----------|--------|
| `test_str_returns_message_for_all_types` | str() 对所有异常返回消息 |
| `test_repr_is_informative` | repr() 提供有用信息 |
| `test_exception_can_be_pickled` | pickle 序列化/反序列化 |

### 5.14 TestProjectSpecCompliance - 规范符合性
| 测试方法 | 验证点 |
|----------|--------|
| `test_error_message_has_location_value` | 所有异常都有 location |
| `test_error_message_is_not_generic` | 消息具有可定位性，非泛泛描述 |
| `test_exception_does_not_swallow_context` | 不吞掉底层上下文 |

## 6. 关键验证要点

### 6.1 RuntimeProcessError 包装真实错误
这是本测试方案的核心关注点。必须验证：
1. 真实执行中故意触发 Python 错误（如调用 None 的属性、访问缺失字典键等）
2. 捕获原始异常并包装为 RuntimeProcessError
3. 包装后的消息包含原始错误的完整信息
4. `original_error` 属性指向原始异常对象
5. Python 异常链 `__cause__` 被正确保留
6. 原始异常的 `__traceback__` 仍然可访问

### 6.2 分层职责验证
- **API 边界层**: 不捕获 InputTypeError，转换为 DATA_ERROR/RUNTIME_ERROR 响应
- **数据模型层**: 使用 InputDataError 进行业务约束检查
- **业务流程层**: 使用 RuntimeProcessError 包装执行失败

### 6.3 消息格式规范
- **InputTypeError**: `<function>: argument '<param>' expects <ExpectedType>, got <ActualType>`
- **InputDataError**: `<Object>.<field_path>: <constraint>, got <value>`
- **RuntimeProcessError**: `<stage>: <high_level_failure>: <original_error>`

## 7. 测试执行后检查清单

大模型生成测试代码后必须验证：
- ✅ 测试文件路径正确 (`tests/unittests/common/test_exceptions.py`)
- ✅ 所有测试类和方法已实现
- ✅ 导入路径正确 (`from src.common.exceptions import ...`)
- ✅ 真实执行场景测试包含故意触发 Python 错误的代码
- ✅ 参数化测试覆盖 7 种以上 Python 异常类型
- ✅ 集成测试验证 API 层职责分离
- ✅ 所有测试可独立运行，不依赖外部状态
