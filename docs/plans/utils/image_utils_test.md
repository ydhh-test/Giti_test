# 图像工具函数测试方案

## 1. 目标

为 `src/utils/image_utils.py` 提供完整的测试覆盖，验证：
- 所有图像处理函数的正确性和鲁棒性
- 异常处理符合项目统一异常体系规范
- 日志记录符合标准化日志模块要求
- 函数间组合使用的正确性
- 边界条件和极端情况的处理

## 2. 测试文件位置

`tests/unittests/utils/test_image_utils.py`

## 3. 导入规范

```python
import base64
import numpy as np
import cv2
from pathlib import Path
from PIL import Image
import tempfile
import pytest

from src.utils.image_utils import (
    base64_to_ndarray,
    ndarray_to_base64, 
    resize_image,
    load_image_to_base64,
    save_base64_to_image,
    convert_cmyk_to_rgb
)
from src.common.exceptions import (
    InputTypeError,
    InputDataError, 
    RuntimeProcessError
)
```

## 4. 测试数据

### 4.1 基础测试图像数据

```python
# 创建测试用的numpy数组（BGR格式）
TEST_IMAGE_ARRAY = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

# 创建对应的base64字符串（带前缀）
_, buffer = cv2.imencode('.png', TEST_IMAGE_ARRAY)
TEST_IMAGE_BASE64_WITH_PREFIX = f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"

# 创建对应的base64字符串（无前缀）
TEST_IMAGE_BASE64_NO_PREFIX = base64.b64encode(buffer).decode('utf-8')

# 支持的图像类型
SUPPORTED_IMAGE_TYPES = ["png", "jpg", "jpeg"]

# 不支持的图像类型  
UNSUPPORTED_IMAGE_TYPES = ["bmp", "tiff", "webp"]
```

### 4.2 无效测试数据

```python
INVALID_BASE64_STRINGS = [
    "invalid_base64_string",
    "data:image/png;base64,invalid",
    "",
    "data:image/bmp;base64,xxx"  # 不支持的格式前缀
]

INVALID_FILE_PATHS = [
    Path("nonexistent_file.png"),
    Path("/root/protected_file.png")  # 权限不足的路径
]
```

## 5. 测试类清单

### 5.1 TestBase64ToNdarray - base64_to_ndarray() 功能测试

| 测试方法 | 验证点 |
|----------|--------|
| `test_valid_base64_with_prefix` | 带data:image前缀的base64正确解码 |
| `test_valid_base64_no_prefix` | 纯base64字符串正确解码 |
| `test_different_image_formats` | PNG、JPG、JPEG格式都支持 |
| `test_input_type_error_non_string` | 非字符串输入抛出InputTypeError |
| `test_input_data_error_invalid_base64` | 无效base64字符串抛出InputDataError |
| `test_input_data_error_unsupported_format` | 不支持的图像格式抛出InputDataError |
| `test_runtime_process_error_memory_issue` | 内存不足等运行时错误抛出RuntimeProcessError |

### 5.2 TestNdarrayToBase64 - ndarray_to_base64() 功能测试

| 测试方法 | 验证点 |
|----------|--------|
| `test_valid_ndarray_to_png` | numpy数组转PNG base64 |
| `test_valid_ndarray_to_jpg` | numpy数组转JPG base64 |
| `test_with_prefix_true` | with_prefix=True返回带前缀字符串 |
| `test_with_prefix_false` | with_prefix=False返回纯base64 |
| `test_input_type_error_non_ndarray` | 非numpy数组输入抛出InputTypeError |
| `test_input_type_error_wrong_ndarray_shape` | 错误形状的数组抛出InputTypeError |
| `test_input_data_error_empty_array` | 空数组抛出InputDataError |
| `test_runtime_process_error_encoding_failure` | 编码失败抛出RuntimeProcessError |

### 5.3 TestResizeImage - resize_image() 功能测试

| 测试方法 | 验证点 |
|----------|--------|
| `test_stretch_mode_exact_dimensions` | stretch模式精确缩放到指定尺寸 |
| `test_width_scale_mode_proportional` | width_scale模式按宽度等比缩放 |
| `test_height_scale_mode_proportional` | height_scale模式按高度等比缩放 |
| `test_grayscale_image_support` | 支持单通道灰度图像 |
| `test_input_type_error_non_ndarray` | 非numpy数组输入抛出InputTypeError |
| `test_input_type_error_invalid_mode` | 无效mode参数抛出InputTypeError |
| `test_input_data_error_zero_dimensions` | 零尺寸抛出InputDataError |
| `test_input_data_error_negative_dimensions` | 负尺寸抛出InputDataError |

### 5.4 TestLoadImageToBase64 - load_image_to_base64() 功能测试

| 测试方法 | 验证点 |
|----------|--------|
| `test_load_png_with_prefix` | 加载PNG文件返回带前缀base64 |
| `test_load_jpg_with_prefix` | 加载JPG文件返回带前缀base64 |
| `test_load_without_prefix` | with_prefix=False返回纯base64 |
| `test_input_type_error_non_path` | 非Path对象输入抛出InputTypeError |
| `test_input_data_error_file_not_found` | 文件不存在抛出InputDataError |
| `test_input_data_error_unsupported_format` | 不支持格式文件抛出InputDataError并记录警告 |
| `test_warning_logged_for_unsupported_format` | 不支持格式触发警告日志 |
| `test_runtime_process_error_permission_denied` | 权限不足抛出RuntimeProcessError |

### 5.5 TestSaveBase64ToImage - save_base64_to_image() 功能测试

| 测试方法 | 验证点 |
|----------|--------|
| `test_save_with_prefix_to_png` | 带前缀base64保存为PNG |
| `test_save_without_prefix_to_png` | 纯base64保存为PNG |
| `test_file_extension_overridden` | 自动修正文件后缀为.png |
| `test_input_type_error_invalid_base64` | 无效base64字符串抛出InputDataError |
| `test_input_type_error_non_path` | 非Path对象输入抛出InputTypeError |
| `test_runtime_process_error_write_permission` | 写入权限不足抛出RuntimeProcessError |
| `test_runtime_process_error_disk_full` | 磁盘空间不足抛出RuntimeProcessError |

### 5.6 TestConvertCmykToRgb - convert_cmyk_to_rgb() 功能测试

| 测试方法 | 验证点 |
|----------|--------|
| `test_valid_cmyk_pil_to_bgr` | CMYK PIL图像正确转换为BGR numpy数组 |
| `test_input_type_error_non_pil_image` | 非PIL Image对象抛出InputTypeError |
| `test_input_type_error_rgb_pil_image` | RGB PIL图像输入抛出InputTypeError |
| `test_input_data_error_corrupted_image` | 损坏的CMYK图像抛出InputDataError |
| `test_runtime_process_error_conversion_failure` | 转换失败抛出RuntimeProcessError |

### 5.7 TestIntegration - 函数集成测试

| 测试方法 | 验证点 |
|----------|--------|
| `test_round_trip_base64_ndarray` | base64 → ndarray → base64 完整往返 |
| `test_load_resize_save_workflow` | load → resize → save 完整工作流 |
| `test_cmyk_convert_save_workflow` | CMYK转换 → 保存完整工作流 |
| `test_multiple_resize_modes_comparison` | 不同缩放模式结果对比验证 |

### 5.8 TestEdgeCases - 边界情况测试

| 测试方法 | 验证点 |
|----------|--------|
| `test_empty_base64_strings` | 空base64字符串处理 |
| `test_very_large_images` | 大尺寸图像处理（内存压力测试） |
| `test_single_pixel_images` | 单像素图像处理 |
| `test_extreme_aspect_ratios` | 极端宽高比图像处理 |
| `test_special_characters_in_paths` | 路径包含特殊字符 |
| `test_unicode_paths` | Unicode路径支持 |

## 6. 关键验证要点

### 6.1 异常处理验证

**InputTypeError验证**：
- 参数类型不符合预期时抛出InputTypeError
- 异常消息格式：`<function>: argument '<param>' expects <ExpectedType>, got <ActualType>`
- 不在API层捕获，直接抛出（编程错误）

**InputDataError验证**：
- 数据内容不符合约束时抛出InputDataError  
- 异常消息格式：`<Object>.<field_path>: <constraint>, got <value>`
- 在API层转换为DATA_ERROR响应

**RuntimeProcessError验证**：
- 运行时执行失败抛出RuntimeProcessError
- 异常消息格式：`<stage>: <high_level_failure>: <original_error>`
- 包装原始异常，保留完整上下文
- 在API层转换为RUNTIME_ERROR响应

### 6.2 日志记录验证

- 使用`src.utils.logger.get_logger()`获取日志记录器
- 不支持格式的文件加载时记录WARNING级别日志
- 日志消息格式符合项目标准：`%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- 避免使用print()语句

### 6.3 图像质量验证

- **base64往返**：确保base64 ↔ ndarray转换不丢失信息
- **格式兼容性**：PNG、JPG、JPEG格式都正确处理
- **颜色空间**：确保BGR/RGB颜色空间转换正确
- **尺寸精度**：resize_image的尺寸计算精确

### 6.4 文件系统验证

- **临时文件管理**：使用tempfile创建临时测试文件
- **自动清理**：测试结束后自动删除临时文件
- **权限处理**：正确处理文件权限相关异常
- **路径处理**：正确处理各种路径格式和特殊字符

## 7. 测试执行后检查清单

大模型生成测试代码后必须验证：
- ✅ 测试文件路径正确 (`tests/unittests/utils/test_image_utils.py`)
- ✅ 所有测试类和方法已实现
- ✅ 导入路径正确 (`from src.utils.image_utils import ...`)
- ✅ 异常类型使用项目统一异常体系
- ✅ 日志记录使用标准化日志模块
- ✅ 使用临时目录进行文件测试，避免污染项目目录
- ✅ 所有测试可独立运行，不依赖外部状态
- ✅ 覆盖所有正常情况、异常情况和边界情况
- ✅ 集成测试验证函数组合使用的正确性

## 8. 特殊注意事项

### 8.1 OpenCV依赖验证

- 确保测试环境中OpenCV正确安装
- 验证cv2.imread/cv2.imwrite对不同格式的支持
- 处理OpenCV可能的编解码器限制

### 8.2 内存管理

- 大图像测试时注意内存使用
- 避免测试过程中内存泄漏
- 及时释放numpy数组和图像对象

### 8.3 平台兼容性

- 路径分隔符处理（Windows vs Unix）
- 文件权限处理差异
- 临时文件创建和清理的跨平台兼容性

### 8.4 与项目架构集成

- 测试应遵循L0-L2项目规范
- 异常处理应符合分层职责要求
- 日志记录应与项目整体日志策略一致
- 不引入项目规范外的额外依赖