"""
模块配置文件
各模块的初始化配置
"""

# 服务模块配置
SERVICES_CONFIG = {
    "analyzer": {
        "enabled": True,
        "default_conf": {
            "target_min": 28.0,
            "target_max": 35.0,
            "margin": 5.0,
        }
    },
    "postprocessor": {
        "enabled": True,
        "rib_count": 5,
    },
}

# 算法模块配置
ALGORITHMS_CONFIG = {
    "detection": {
        "pattern_continuity": {
            "enabled": False,
        }
    },
    "stitching": {
        "vertical_stitch": {
            "enabled": False,
        }
    }
}

# 工具模块配置
UTILS_CONFIG = {
    "cv_utils": {
        "default_blend_width": 10,
    },
    "logger": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    }
}
