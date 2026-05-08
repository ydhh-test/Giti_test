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
    """将 base64 字符串解码为 BGR np.ndarray。
    入参 image_base64 允许包含 "data:image/png;base64," 前缀，函数内部去除。
    依赖：base64.b64decode + np.frombuffer + cv2.imdecode"""
    # 实现
    import base64
    import numpy as np
    import cv2

    # 去除前缀
    if image_base64.startswith("data:image/png;base64,"):
        image_base64 = image_base64[len("data:image/png;base64,"):] 

    # 解码
    image_data = base64.b64decode(image_base64)
    image_array = np.frombuffer(image_data, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    return image
```

### 4.2 ndarray_to_base64
```python
def ndarray_to_base64(
    image: np.ndarray, 
    image_type: ImageType = "png", 
    with_prefix: bool = True
) -> str:
    """将 BGR np.ndarray 编码为 base64 字符串。
    依赖：cv2.imencode + base64.b64encode
    with_prefix=True 时返回 "data:image/png;base64,xxx"。"""
    # 实现
    import base64
    import cv2

    # 编码
    _, buffer = cv2.imencode(f".{image_type}", image)
    image_base64 = base64.b64encode(buffer).decode('utf-8')

    if with_prefix:
        image_base64 = f"data:image/{image_type};base64,{image_base64}"

    return image_base64
```

### 4.3 resize_image
```python
def resize_image(
    image: np.ndarray,
    target_width: int,
    target_height: int | None = None,
    mode: ResizeMode = "stretch"
) -> np.ndarray:
    """系统统一图像缩放工具函数
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
        np.ndarray: 缩放后的图像"""
    # 实现
    import cv2

    h, w = image.shape[:2]

    if mode == "stretch":
        resized_image = cv2.resize(image, (target_width, target_height or h))
    elif mode == "width_scale":
        scale_factor = target_width / w
        new_height = int(h * scale_factor)
        resized_image = cv2.resize(image, (target_width, new_height))
    elif mode == "height_scale":
        scale_factor = (target_height or h) / h
        new_width = int(w * scale_factor)
        resized_image = cv2.resize(image, (new_width, target_height or h))

    return resized_image
```

### 4.4 load_image_to_base64
```python
def load_image_to_base64(file_path: Path, with_prefix: bool = True) -> str:
    """读取 图片文件 并直接转为 base64。
    至少支持 png、jpg等常见格式（除了png，都要报告warning）"""
    # 实现
    import base64
    from pathlib import Path
    import cv2

    # 读取图片
    image = cv2.imread(str(file_path))

    if image is None:
        raise FileNotFoundError(f"无法读取图片文件: {file_path}")

    # 获取文件扩展名
    file_extension = file_path.suffix.lower()

    if file_extension not in [".png", ".jpg", ".jpeg"]:
        print(f"警告: 不支持的文件格式: {file_extension}")

    # 编码为 base64
    _, buffer = cv2.imencode(file_extension, image)
    image_base64 = base64.b64encode(buffer).decode('utf-8')

    if with_prefix:
        image_base64 = f"data:image/{file_extension[1:]};base64,{image_base64}"

    return image_base64
```

### 4.5 save_base64_to_image
```python
def save_base64_to_image(base64_str: str, save_path: Path, with_prefix: bool = True) -> None:
    """将图片base64字符串解码后保存为本地文件，**强制存储格式为PNG**。
    自动修正文件后缀为.png，忽略原路径后缀；
    兼容带data:image前缀和纯base64字符串。"""
    # 实现
    import base64
    from pathlib import Path
    import cv2

    # 去除前缀
    if with_prefix and base64_str.startswith("data:image/"):
        base64_str = base64_str.split(",")[1]

    # 解码
    image_data = base64.b64decode(base64_str)
    image_array = np.frombuffer(image_data, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    # 保存为 PNG 格式
    save_path = save_path.with_suffix(".png")
    cv2.imwrite(str(save_path), image)
```

### 4.6 convert_cmyk_to_rgb
```python
def convert_cmyk_to_rgb(img_pil) -> np.ndarray:
    """将PIL CMYK图像转换为OpenCV BGR格式（内存转换，无需文件IO）    
    Args:
        img_pil: PIL Image对象 (CMYK模式)    
    Returns:
        numpy数组 (BGR格式)"""
    # 实现
    from PIL import Image
    import numpy as np
    import cv2

    # 转换为 RGB
    img_rgb = img_pil.convert("RGB")

    # 转换为 OpenCV BGR 格式
    img_bgr = cv2.cvtColor(np.array(img_rgb), cv2.COLOR_RGB2BGR)

    return img_bgr
```