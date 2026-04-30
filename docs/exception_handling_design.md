# 项目异常管理设计

## 1. 目标

本文档定义项目中的异常管理方式，目标是：

- 避免异常处理逻辑散落在各个文件中各自约定
- 统一异常分类
- 统一异常信息格式
- 明确数据模型层、业务层、API 边界层的异常职责
- 为后续 API、模型、流程层的统一异常处理提供基础

---

## 2. 核心原则

### 2.1 异常分类集中定义
异常类型应集中定义，不应在各个文件中随意发明和分散维护。

### 2.2 校验与错误协议分层
- 数据模型层负责结构与约束检查
- API 边界层负责将内部异常统一映射为标准错误输出
- 业务流程层负责业务执行异常，不负责最终对外错误协议

### 2.3 类型错误与业务错误分离
- 参数类型错误、调用方式错误应优先视为编程错误
- 业务输入不合法应视为业务错误
- 运行时执行失败应归类为运行时错误

### 2.4 异常信息必须可定位
异常信息必须带有定位价值，不允许只提供泛泛描述。

### 2.5 底层异常上下文不得丢失
运行时异常应尽量保留原始报错信息，不应吞掉底层错误上下文。

---

## 3. 异常分类

推荐的最小异常层级如下：

```python
ProjectError
├── InputError
│   ├── InputTypeError
│   └── InputDataError
└── RuntimeProcessError
```

### 3.1 ProjectError
项目级统一异常基类。

### 3.2 InputError
输入相关错误的父类。

### 3.3 InputTypeError
用于表示函数收到的参数类型不符合约定。

适用场景：
- 函数要求接收某类模型实例，实际收到其他类型对象

这类错误属于：
- 编程错误
- 调用方式错误

不应映射为业务失败响应对象。

### 3.4 InputDataError
用于表示输入对象类型正确，但其数据内容不满足约束。

适用场景：
- 字段缺失
- 字段值不满足约束
- 请求态对象状态非法

这类错误通常可映射为：
- `DATA_ERROR`

### 3.5 RuntimeProcessError
用于表示执行过程失败，且问题不在输入本身。

适用场景：
- 构造响应时内部异常
- 执行流程中意外失败
- 下层调用失败

这类错误通常可映射为：
- `RUNTIME_ERROR`

---

## 4. 异常信息格式要求

### 4.1 InputTypeError 必须包含
- 函数名
- 参数名
- 期望类型
- 实际类型

推荐输出格式：

```text
<function>: argument '<param>' expects <ExpectedType>, got <ActualType>
```

示例：

```text
generate_big_image_with_evaluation: argument 'tire_struct' expects FakeTireStruct, got dict
```

### 4.2 InputDataError 必须包含
- 对象名
- 字段路径
- 违反的规则
- 必要时包含实际值

推荐输出格式：

```text
<Object>.<field_path>: <constraint>, got <value>
```

示例：

```text
FakeTireStruct.scheme_rank: must be >= 1, got 0
```

```text
FakeTireStruct.big_image: must be None in request, got {'image_base64': 'xxx'}
```

### 4.3 RuntimeProcessError 必须包含
- 执行阶段或函数名
- 高层失败说明
- 原始异常信息

推荐输出格式：

```text
<stage>: <high_level_failure>: <original_error>
```

示例：

```text
create_success_response: failed to build fake big image: 'NoneType' object has no attribute 'rule6_1'
```

---

## 5. 结构化字段建议

项目异常对象建议至少支持以下字段：

- `message`
- `location`
- `details`
- `cause`

不同异常类型可追加自身字段，例如：

### InputTypeError
- `function`
- `param`
- `expected_type`
- `actual_type`

### InputDataError
- `object_name`
- `field_path`
- `rule`
- `actual_value`

### RuntimeProcessError
- `stage`

要求：
- `str(exception)` 必须直接可读
- 异常对象内部应尽量保留结构化上下文，供 API 层或日志层使用

---

## 6. 分层职责

### 6.1 数据模型层
负责：
- 结构合法性检查
- 字段约束检查
- 请求态对象约束检查（如果该模型承担请求语义）

不负责：
- 错误码协议
- 对外响应格式

### 6.2 业务流程层
负责：
- 执行业务逻辑
- 抛出或传播运行时异常

不负责：
- 最终对外错误协议

### 6.3 API 边界层
负责：
- 检查函数边界输入
- 捕获项目内异常
- 将异常统一映射为标准输出结构
- 区分：
  - 类型错误
  - 业务输入错误
  - 运行时错误

---

## 7. 边界处理规则

### 7.1 参数类型错误
- 视为编程错误
- 直接抛异常
- 不转换成业务错误响应

### 7.2 数据内容错误
- 视为业务输入错误
- 在 API 边界层转换为标准错误响应
- 通常映射为 `DATA_ERROR`

### 7.3 运行时错误
- 视为执行错误
- 在 API 边界层统一映射
- 通常映射为 `RUNTIME_ERROR`

---

## 8. 与项目规范的关系

本设计文档是对以下项目规范的补充细化：

- `docs/project_coding_standards.md`
- `docs/project_coding_standards_agent.md`

执行时仍应同时遵守项目级架构、模型、API、测试与依赖管理规范。

---

## 9. 当前推荐做法

当前项目阶段推荐采用轻量异常体系：

- 使用集中定义的少量异常类型
- 模型层负责检查
- API 边界层负责统一映射
- 不引入过重的异常框架
- 不在多个文件中重复实现同类错误映射规则

---

**文档结束**
