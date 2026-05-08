# 异常类使用指南

## 1. 概述

本文档指导开发者在设计和实现新功能时如何正确使用项目中的通用异常类。异常体系是项目架构的重要组成部分，确保错误处理的一致性和可维护性。

## 2. 异常类导入

所有异常类位于`src/common/exceptions.py`，使用以下方式导入：

```python
from common.exceptions import (
    ProjectError,
    InputError, 
    InputTypeError,
    InputDataError,
    RuntimeProcessError
)
```

## 3. 使用场景分类

### 3.1 InputTypeError - 类型错误（编程错误）

**适用场景**：
- 函数参数类型不符合预期
- 调用方式错误
- 传入了错误的数据类实例

**使用位置**：API边界层、公共函数入口

**处理方式**：直接抛出，不转换为业务响应

**示例**：
```python
def process_tire_data(data: TireStruct) -> TireStruct:
    if not isinstance(data, TireStruct):
        raise InputTypeError(
            function="process_tire_data",
            param="data",
            expected_type="TireStruct", 
            actual_type=type(data).__name__
        )
    # 继续处理...
```

### 3.2 InputDataError - 数据错误（业务错误）

**适用场景**：
- 数据对象字段值不满足业务约束
- 请求数据违反业务规则
- 字段缺失或格式错误

**使用位置**：数据模型层的校验方法中

**处理方式**：在API层转换为`DATA_ERROR`响应

**示例**：
```python
class TireStruct(BaseModel):
    def validate_request(self) -> str | None:
        if self.scheme_rank is not None and self.scheme_rank < 1:
            error = InputDataError(
                object_name="TireStruct",
                field_path="scheme_rank",
                rule="must be >= 1",
                actual_value=self.scheme_rank
            )
            return str(error)
        return None
```

### 3.3 RuntimeProcessError - 运行时错误

**适用场景**：
- 业务逻辑执行失败
- 下层调用异常
- 构造响应时内部错误

**使用位置**：业务流程层、核心执行逻辑

**处理方式**：在API层转换为`RUNTIME_ERROR`响应

**示例**：
```python
def execute_pipeline(data: TireStruct) -> TireStruct:
    try:
        # 执行复杂业务逻辑
        result = complex_business_logic(data)
        return result
    except Exception as original_error:
        raise RuntimeProcessError(
            stage="execute_pipeline",
            high_level_failure="pipeline execution failed",
            original_error=original_error
        )
```

## 4. 分层职责实现

### 4.1 API边界层实现模式

```python
def api_endpoint(request_data: RequestModel) -> ResponseModel:
    # 1. 类型检查 - InputTypeError
    if not isinstance(request_data, RequestModel):
        raise InputTypeError(...)  # 编程错误，直接抛出
    
    # 2. 数据校验 - InputDataError  
    validation_error = request_data.validate_request()
    if validation_error:
        return create_error_response("DATA_ERROR", validation_error)
    
    # 3. 业务执行 - RuntimeProcessError
    try:
        return execute_business_logic(request_data)
    except RuntimeProcessError as e:
        return create_error_response("RUNTIME_ERROR", str(e))
    except Exception as e:
        # 包装未预期异常
        runtime_error = RuntimeProcessError(
            stage="api_endpoint",
            high_level_failure="unexpected error in business logic",
            original_error=e
        )
        return create_error_response("RUNTIME_ERROR", str(runtime_error))
```

### 4.2 数据模型层实现模式

```python
class BusinessModel(BaseModel):
    field_a: int
    field_b: str
    
    def validate_request(self) -> str | None:
        """返回错误消息字符串，或None表示无错误"""
        # 检查field_a范围
        if self.field_a < 0:
            error = InputDataError(
                object_name=self.__class__.__name__,
                field_path="field_a", 
                rule="must be non-negative",
                actual_value=self.field_a
            )
            return str(error)
            
        # 检查field_b长度
        if len(self.field_b) == 0:
            error = InputDataError(
                object_name=self.__class__.__name__,
                field_path="field_b",
                rule="must not be empty",
                actual_value=self.field_b
            )
            return str(error)
            
        return None
```

## 5. 最佳实践

### 5.1 字段路径命名
- 使用简洁明确的字段名：`"small_images"`、`"scheme_rank"`
- 对嵌套对象使用点号表示法：`"big_image.meta.width"`
- 避免使用模糊或技术性过强的路径名

### 5.2 实际值处理
- 基础类型直接使用：`actual_value=5`
- 复杂对象使用`.model_dump()`：`actual_value=obj.model_dump()`
- 避免传递整个对象引用，防止序列化问题

### 5.3 错误消息清晰性
- 规则描述要具体：`"must be >= 1"` 而不是 `"invalid value"`
- 阶段描述要有意义：`"create_success_response"` 而不是 `"stage1"`

### 5.4 异常包装原则
- 始终保留原始异常上下文
- 高层失败描述要概括性：`"failed to build fake big image"`
- 避免重复包装同一异常

## 6. 常见错误避免

### 6.1 不要在数据模型层抛出InputTypeError
❌ 错误：
```python
class Model(BaseModel):
    def some_method(self, param):
        if not isinstance(param, ExpectedType):
            raise InputTypeError(...)  # 应该在API层检查
```

✅ 正确：
```python
# API层检查类型
def api_function(model: Model, param: ExpectedType):
    if not isinstance(param, ExpectedType):
        raise InputTypeError(...)
    
    # 数据模型层只处理数据内容校验
    model.process_with_param(param)  # 假设param类型已验证
```

### 6.2 不要吞掉原始异常信息
❌ 错误：
```python
try:
    risky_operation()
except Exception:
    raise RuntimeProcessError("stage", "something failed", Exception())  # 丢失原始异常
```

✅ 正确：
```python
try:
    risky_operation()
except Exception as original_error:
    raise RuntimeProcessError("stage", "something failed", original_error)  # 保留原始异常
```

## 7. 与项目规范的关系

- 本指南必须与`docs/exception_handling_design.md`保持一致
- 异常使用必须符合L0架构边界要求
- 错误处理必须遵循L1错误处理标准
- 文档更新时必须同步更新相关设计文档