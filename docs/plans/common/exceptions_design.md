# 通用异常类设计方案

## 1. 设计目标

本文档为大模型提供完整的异常类设计规范，确保生成的代码符合项目架构要求。目标包括：
- 提供统一的异常分类体系
- 确保异常信息具有可定位性
- 支持分层职责分离（API层、数据模型层、业务层）
- 为后续统一异常处理提供基础

## 2. 异常层次结构

### 2.1 完整继承体系
```python
ProjectError
├── InputError
│   ├── InputTypeError
│   └── InputDataError
└── RuntimeProcessError
```

### 2.2 文件位置
- **文件路径**: `src/common/exceptions.py`
- **导入方式**: `from common.exceptions import [ExceptionClass]`

## 3. 异常类详细规范

### 3.1 ProjectError (基类)
- **用途**: 项目级统一异常基类
- **结构化字段**: 
  - `message`: 错误消息
  - `location`: 错误位置
  - `details`: 详细信息字典
  - `cause`: 原始异常（可选）
- **要求**: 所有自定义异常必须继承此类

### 3.2 InputTypeError
- **用途**: 参数类型错误（编程错误）
- **适用场景**: 函数收到的参数类型不符合约定
- **结构化字段**:
  - `function`: 函数名
  - `param`: 参数名  
  - `expected_type`: 期望类型
  - `actual_type`: 实际类型
- **消息格式**: `<function>: argument '<param>' expects <ExpectedType>, got <ActualType>`
- **处理规则**: 视为编程错误，不转换为业务失败响应，直接抛出

### 3.3 InputDataError  
- **用途**: 输入数据内容错误（业务错误）
- **适用场景**: 数据对象类型正确但内容不满足约束
- **结构化字段**:
  - `object_name`: 对象名
  - `field_path`: 字段路径（支持点号表示法）
  - `rule`: 违反的规则描述
  - `actual_value`: 实际值（可选）
- **消息格式**: `<Object>.<field_path>: <constraint>, got <value>`
- **处理规则**: 视为业务错误，在API边界层转换为`DATA_ERROR`响应

### 3.4 RuntimeProcessError
- **用途**: 运行时执行失败
- **适用场景**: 执行过程失败且问题不在输入本身
- **结构化字段**:
  - `stage`: 执行阶段或函数名
  - `original_error`: 原始异常对象
- **消息格式**: `<stage>: <high_level_failure>: <original_error>`
- **处理规则**: 视为运行时错误，在API边界层转换为`RUNTIME_ERROR`响应

## 4. 分层使用规范

### 4.1 API边界层职责
- **类型检查**: 使用`InputTypeError`验证函数参数是否为正确的数据类实例
- **异常捕获**: 捕获`InputDataError`和`RuntimeProcessError`并转换为标准错误响应
- **不处理**: 不捕获`InputTypeError`（让其作为编程错误向上抛出）

### 4.2 数据模型层职责  
- **数据校验**: 在数据类中使用`InputDataError`进行业务约束检查
- **字段路径**: 使用精确的字段路径，如`"small_images"`、`"big_image.meta.width"`
- **实际值**: 对复杂对象使用`.model_dump()`获取可读的实际值

### 4.3 业务流程层职责
- **异常包装**: 使用`RuntimeProcessError`包装原始异常，保留上下文
- **阶段标识**: 明确标识执行阶段，便于问题定位

## 5. 大模型执行指导

### 5.1 何时使用哪种异常
- **检查参数类型**: 使用`InputTypeError`
- **检查数据内容**: 使用`InputDataError`  
- **处理执行失败**: 使用`RuntimeProcessError`

### 5.2 构造异常实例
```python
# InputTypeError示例
raise InputTypeError(
    function="process_request",
    param="data",
    expected_type="FakeTireStruct",
    actual_type=type(data).__name__
)

# InputDataError示例  
raise InputDataError(
    object_name="FakeTireStruct",
    field_path="scheme_rank",
    rule="must be >= 1",
    actual_value=self.scheme_rank
)

# RuntimeProcessError示例
raise RuntimeProcessError(
    stage="create_success_response",
    high_level_failure="failed to build fake big image", 
    original_error=error
)
```

### 5.3 异常处理模式
```python
# API层标准异常处理模式
def api_function(data: DataClass) -> DataClass:
    # 1. 类型检查
    if not isinstance(data, DataClass):
        raise InputTypeError(...)  # 不捕获
    
    # 2. 数据校验
    err_msg = data.validate_request()
    if err_msg:
        return create_error_response(data, "DATA_ERROR", err_msg)
    
    # 3. 业务执行
    try:
        return create_success_response(data)
    except Exception as e:
        runtime_error = RuntimeProcessError(...)
        return create_error_response(data, "RUNTIME_ERROR", str(runtime_error))
```

## 6. 验证要点

大模型生成代码后必须验证：
- ✅ 异常类导入路径正确 (`from common.exceptions import ...`)
- ✅ 异常构造参数完整且符合规范
- ✅ 消息格式与项目要求一致
- ✅ 分层职责符合架构边界要求
- ✅ 数据类字段路径准确无误