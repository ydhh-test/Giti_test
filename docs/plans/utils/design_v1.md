# 公共函数设计方案 v1

## 1. 设计目标

实现一组可迁移的公共图像处理函数，符合项目编码规范，支持未来在其他项目中直接复用。

## 2. 文件组织

### 2.1 图像处理工具函数
- **文件路径**: `src/utils/image_utils.py`
- **包含函数**: 
  - `base64_to_ndarray()`
  - `ndarray_to_base64()`
  - `resize_image()`
  - `load_image_to_base64()`
  - `save_base64_to_image()`
  - `convert_cmyk_to_rgb()`

### 2.2 轮胎结构工具函数
- **文件路径**: `src/utils/tire_utils.py`
- **包含函数**: 
  - `default_tire_struct()`

### 2.3 异常定义
- **文件路径**: `src/utils/exceptions.py`
- **包含类**:
  - `ImageProcessingError`
  - `InputTypeError`
  - `InputDataError`
  - `RuntimeProcessError`

### 2.4 日志工具
- **文件路径**: `src/utils/logger.py`
- **由研发工程师自行实现**

## 3. 类型定义策略

为保证公共函数的可迁移性，不使用项目特定枚举，改用字符串字面量类型：

```python
from typing import Literal

ImageType = Literal["png", "jpg", "jpeg"]
ResizeMode = Literal["stretch", "width_scale", "height_scale"]
```

## 4. 函数签名定义

### 4.1 base64_to_ndarray
```python
def base64_to_ndarray(image_base64: str) -> np.ndarray:
    """
    将 base64 字符串解码为 BGR np.ndarray。
    入参 image_base64 允许包含 "data:image/png;base64," 前缀，函数内部去除。
    依赖：base64.b64decode + np.frombuffer + cv2.imdecode
    """
```

### 4.2 ndarray_to_base64
```python
def ndarray_to_base64(
    image: np.ndarray, 
    image_type: ImageType = "png", 
    with_prefix: bool = True
) -> str:
    """
    将 BGR np.ndarray 编码为 base64 字符串。
    依赖：cv2.imencode + base64.b64encode
    with_prefix=True 时返回 "data:image/png;base64,xxx"。
    """
```

### 4.3 resize_image
```python
def resize_image(
    image: np.ndarray,
    target_width: int,
    target_height: int | None = None,
    mode: ResizeMode = "stretch"
) -> np.ndarray:
    """
    系统统一图像缩放工具函数
    输入图像必须为 np.ndarray 格式，shape 遵循 (H, W, C) 或 (H, W) 规范

    Parameters:
        image (np.ndarray): 输入原始图像，仅支持 numpy 数组
        target_width (int): 目标输出宽度
        target_height (int | None): 目标输出高度
        mode (ResizeMode): 图像缩放模式
            - "stretch": 普通缩放，直接按指定宽高拉伸/缩放到目标尺寸
            - "width_scale": 以目标宽度为基准，按原图比例等比缩放，高度自适应
            - "height_scale": 以目标高度为基准，按原图比例等比缩放，宽度自适应

    Returns:
        np.ndarray: 缩放后的图像
    """
```

### 4.4 load_image_to_base64
```python
def load_image_to_base64(file_path: Path, with_prefix: bool = True) -> str:
    """
    读取 图片文件 并直接转为 base64。
    至少支持 png、jpg等常见格式（除了png，都要报告warning）
    """
```

### 4.5 save_base64_to_image
```python
def save_base64_to_image(base64_str: str, save_path: Path, with_prefix: bool = True) -> None:
    """
    将图片base64字符串解码后保存为本地文件，**强制存储格式为PNG**。
    自动修正文件后缀为.png，忽略原路径后缀；
    兼容带data:image前缀和纯base64字符串。
    """
```

### 4.6 convert_cmyk_to_rgb
```python
def convert_cmyk_to_rgb(img_pil) -> np.ndarray:
    """
    将PIL CMYK图像转换为OpenCV BGR格式（内存转换，无需文件IO）    
    Args:
        img_pil: PIL Image对象 (CMYK模式)    
    Returns:
        numpy数组 (BGR格式)
    """
```

### 4.7 default_tire_struct
```python
def default_tire_struct() -> TireStruct:
    """按照默认输入，实现完整输入实例"""
```

## 5. 异常处理规范

所有函数遵循统一的异常处理策略：

- **InputTypeError**: 参数类型错误，视为编程错误
- **InputDataError**: 输入数据内容错误，视为业务错误  
- **RuntimeProcessError**: 运行时执行错误

异常消息格式遵循项目规范：
- InputTypeError: `<function>: argument '<param>' expects <ExpectedType>, got <ActualType>`
- InputDataError: `<Object>.<field_path>: <constraint>, got <value>`
- RuntimeProcessError: `<stage>: <high_level_failure>: <original_error>`

## 6. 依赖要求

现有依赖版本满足需求，无需修改：
- `numpy>=1.24.0`
- `opencv-python>=4.8.0`
- `Pillow>=10.0.0`

## 7. 实现约束

- 所有函数参数使用显式基本类型，不使用数据类包装
- 图像处理函数保持无项目依赖，确保可迁移性
- `default_tire_struct()` 函数可以依赖项目模型
- 遵循项目L1强制标准和L0不可违反标准
- 每个函数负责自己的参数边界校验

## 8. 后续步骤

1. 实现 `src/utils/exceptions.py`
2. 实现 `src/utils/image_utils.py` 
3. 实现 `src/utils/tire_utils.py`
4. 集成日志工具到 `src/utils/logger.py`
5. 编写单元测试
6. 验证依赖兼容性