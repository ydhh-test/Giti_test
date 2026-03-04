# -*- coding: utf-8 -*-

"""
规则配置模块

提供规则相关的配置参数。
"""

# Copyright © 2026 云端辉鸿. All rights reserved.
# Author: 桂禹 <guiyu@cloudhuihong.com>
# AI Assistant: ClaudeCode (Claude Sonnet 4)

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class PatternContinuityConfig:
    """图案连续性检测配置"""

    # 评分
    score: int = 10

    # 固定灰度阈值
    threshold: int = 200

    # 边缘区域高度（像素）
    edge_height: int = 4

    # 粗细线宽度阈值（像素）
    coarse_threshold: int = 5

    # 细线匹配的最大距离（像素）
    fine_match_distance: int = 4

    # 粗线匹配的最小重合比例
    coarse_overlap_ratio: float = 0.67

    # 是否使用自适应阈值
    use_adaptive_threshold: bool = False

    # 自适应方法：'otsu'或'adaptive'
    adaptive_method: str = 'otsu'

    # 最小线条宽度（过滤噪音）
    min_line_width: int = 1

    # 连通性判定（4或8）
    connectivity: int = 4

    # 可视化线条宽度
    vis_line_width: int = 2

    # 可视化字体大小
    vis_font_scale: float = 0.5

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'PatternContinuityConfig':
        """从配置字典创建对象"""
        return cls(**{k: v for k, v in conf.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'score': self.score,
            'threshold': self.threshold,
            'edge_height': self.edge_height,
            'coarse_threshold': self.coarse_threshold,
            'fine_match_distance': self.fine_match_distance,
            'coarse_overlap_ratio': self.coarse_overlap_ratio,
            'use_adaptive_threshold': self.use_adaptive_threshold,
            'adaptive_method': self.adaptive_method,
            'min_line_width': self.min_line_width,
            'connectivity': self.connectivity,
            'vis_line_width': self.vis_line_width,
            'vis_font_scale': self.vis_font_scale,
        }
