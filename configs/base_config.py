"""
基础配置文件
包含路径、海陆比评分规则等基础配置
"""

# 路径配置
PATHS = {
    "data_dir": r"D:\云端辉宏\佳通轮胎\后处理\giti-tire-ai-pattern\.results\data",
    "test_data_dir": r"D:\云端辉宏\佳通轮胎\后处理\giti-tire-ai-pattern\tests\test_data",
    "output_dir": r"D:\云端辉宏\佳通轮胎\后处理\giti-tire-ai-pattern\.results",
    "logs_dir": r"D:\云端辉宏\佳通轮胎\后处理\giti-tire-ai-pattern\.logs",
}

# 海陆比评分规则配置
LAND_SEA_RULES = {
    "target_min": 28.0,      # 目标最小值(%)
    "target_max": 35.0,     # 目标最大值(%)
    "margin": 5.0,          # 容差范围
    "black_pixel_rl": 0,    # 黑色像素下限
    "black_pixel_rr": 50,   # 黑色像素上限
    "gray_pixel_rl": 51,    # 灰色像素下限
    "gray_pixel_rr": 200,  # 灰色像素上限
}

# 默认配置字典（用于main.py）
DEFAULT_CONF = {
    "target_min": 28.0,
    "target_max": 35.0,
    "margin": 5.0,
    "black_pixel_rl": 0,
    "black_pixel_rr": 50,
    "gray_pixel_rl": 51,
    "gray_pixel_rr": 200
}

# 图片文件扩展名
VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tif')
