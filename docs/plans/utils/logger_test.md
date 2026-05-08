# 日志模块测试方案

## 1. 目标

为 `src/utils/logger.py` 提供完整的测试覆盖，验证：
- 日志记录器的正确配置和创建
- 文件和控制台输出功能
- 日志级别控制
- LoggerMixin 类的正确集成
- 默认日志记录器的功能
- 避免重复处理器的问题

## 2. 测试文件位置

`tests/unittests/utils/test_logger.py`

## 3. 导入规范

```python
import logging
import tempfile
import os
from pathlib import Path
from src.utils.logger import setup_logger, get_logger, LoggerMixin, default_logger
```

## 4. 测试数据

```python
TEST_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOGGER_NAME = "tire-ai-pattern"
```

## 5. 测试类清单

### 5.1 TestSetupLogger - setup_logger() 功能测试
| 测试方法 | 验证点 |
|----------|--------|
| `test_setup_logger_default_config` | 默认参数创建日志记录器 |
| `test_setup_logger_custom_name` | 自定义名称 |
| `test_setup_logger_custom_level` | 自定义日志级别 |
| `test_setup_logger_file_output` | 文件输出功能 |
| `test_setup_logger_console_output_disabled` | 控制台输出禁用 |
| `test_setup_logger_both_outputs` | 文件和控制台同时输出 |
| `test_setup_logger_invalid_level` | 无效日志级别处理 |
| `test_setup_logger_creates_log_directory` | 自动创建日志目录 |

### 5.2 TestGetLogger - get_logger() 功能测试
| 测试方法 | 验证点 |
|----------|--------|
| `test_get_logger_returns_existing` | 返回已存在的记录器 |
| `test_get_logger_creates_new` | 创建新记录器（无处理器时） |
| `test_get_logger_same_name_same_instance` | 同名返回同一实例 |
| `test_get_logger_different_names_different_instances` | 不同名称返回不同实例 |

### 5.3 TestLoggerMixin - LoggerMixin 类测试
| 测试方法 | 验证点 |
|----------|--------|
| `test_logger_mixin_property` | logger 属性返回正确记录器 |
| `test_logger_mixin_class_name_as_logger_name` | 使用类名作为记录器名称 |
| `test_logger_mixin_multiple_instances_share_logger` | 多个实例共享同一记录器 |
| `test_logger_mixin_inheritance` | 继承 LoggerMixin 的子类正确工作 |

### 5.4 TestDefaultLogger - 默认日志记录器测试
| 测试方法 | 验证点 |
|----------|--------|
| `test_default_logger_exists` | default_logger 存在 |
| `test_default_logger_correct_name` | 名称为 "tire-ai-pattern" |
| `test_default_logger_has_handlers` | 已配置处理器 |

### 5.5 TestLoggingFunctionality - 日志功能测试
| 测试方法 | 验证点 |
|----------|--------|
| `test_log_levels_filtering` | 日志级别过滤正确 |
| `test_log_message_format` | 日志消息格式正确 |
| `test_log_to_file_content` | 文件日志内容正确 |
| `test_log_to_console_capture` | 控制台日志可捕获验证 |

### 5.6 TestEdgeCases - 边界情况测试
| 测试方法 | 验证点 |
|----------|--------|
| `test_setup_logger_no_duplicate_handlers` | 避免重复添加处理器 |
| `test_logger_with_special_characters_in_name` | 记录器名称包含特殊字符 |
| `test_logger_with_empty_name` | 空名称处理 |
| `test_concurrent_logger_creation` | 并发创建记录器的安全性 |

## 6. 关键验证要点

### 6.1 文件输出验证
- 创建临时目录进行文件日志测试
- 验证日志文件内容包含正确的格式：`%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- 验证日志级别过滤正确（如 INFO 级别不输出 DEBUG 消息）

### 6.2 控制台输出验证
- 使用 pytest 的 caplog fixture 或 StringIO 捕获控制台输出
- 验证输出内容和格式正确

### 6.3 处理器重复问题
- 验证多次调用 `setup_logger()` 不会重复添加处理器
- 验证 `get_logger()` 正确检测已配置的处理器

### 6.4 LoggerMixin 集成
- 验证混入类正确提供 logger 属性
- 验证不同类使用不同的记录器名称
- 验证同一个类的多个实例共享记录器

### 6.5 异常处理
- 验证无效日志级别参数的处理
- 验证文件路径权限问题的处理
- 验证日志目录创建失败的处理

## 7. 测试执行后检查清单

大模型生成测试代码后必须验证：
- ✅ 测试文件路径正确 (`tests/unittests/utils/test_logger.py`)
- ✅ 所有测试类和方法已实现
- ✅ 使用临时目录进行文件日志测试，避免污染项目目录
- ✅ 正确处理日志记录器的全局状态（可能需要在测试前后清理）
- ✅ 验证日志消息格式和内容
- ✅ 所有测试可独立运行，不依赖外部状态
- ✅ 覆盖所有日志级别和输出组合

## 8. 特殊注意事项

### 8.1 全局状态管理
Python logging 模块使用全局状态，测试需要注意：
- 在测试开始前清理相关的日志记录器
- 在测试结束后恢复原始状态
- 使用唯一的记录器名称避免测试间干扰

### 8.2 临时文件管理
- 使用 `tempfile.TemporaryDirectory()` 创建临时日志目录
- 确保临时文件在测试结束后自动清理
- 验证日志文件的创建和内容读取

### 8.3 并发安全性
- 虽然单线程测试，但要考虑日志模块的线程安全设计
- 验证在多实例场景下的正确行为

### 8.4 与异常处理集成
- 测试日志与异常处理的配合使用
- 验证 `exc_info=True` 参数的正确使用
- 验证异常上下文的完整记录