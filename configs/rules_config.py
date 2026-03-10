"""
规则配置文件
包含海陆比计算规则、评分标准等
"""

# 海陆比评分规则
LAND_SEA_RATIO_RULES = {
    # 目标区间（百分比）
    "target_min": 28.0,
    "target_max": 35.0,
    # 容差范围
    "margin": 5.0,
}

# 像素阈值配置
PIXEL_THRESHOLDS = {
    # 黑色像素（深沟槽）
    "black": {
        "min": 0,
        "max": 50,
    },
    # 灰色像素（浅沟槽/细花）
    "gray": {
        "min": 51,
        "max": 200,
    },
    # 白色像素（胎面）
    "white": {
        "min": 201,
        "max": 255,
    }
}

# 评分标准
SCORING_RULES = {
    # 优秀：落在目标区间内
    "excellent_score": 2,
    # 及格：落在容差范围内
    "passable_score": 1,
    # 不合格：超出容差范围
    "fail_score": 0,
}

# 评分详情
SCORE_DESCRIPTIONS = {
    2: "优秀 - 海陆比在目标区间内",
    1: "及格 - 海陆比在容差范围内",
    0: "不合格 - 海陆比超出容差范围",
}
