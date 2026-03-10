"""
异常处理模块
定义项目自定义异常类
"""


class TireAIError(Exception):
    """项目基础异常类"""
    pass


class ConfigError(TireAIError):
    """配置相关异常"""
    pass


class ImageProcessError(TireAIError):
    """图像处理异常"""
    pass


class ImageReadError(ImageProcessError):
    """图像读取异常"""
    pass


class ImageSaveError(ImageProcessError):
    """图像保存异常"""
    pass


class InvalidImageError(ImageProcessError):
    """无效图像异常"""
    pass


class AlgorithmError(TireAIError):
    """算法执行异常"""
    pass


class ValidationError(TireAIError):
    """数据验证异常"""
    pass


class FileNotFoundError(TireAIError):
    """文件不存在异常"""
    pass
