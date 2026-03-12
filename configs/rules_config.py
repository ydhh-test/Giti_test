# -*- coding: utf-8 -*-

"""
规则配置模块

提供规则相关的配置参数。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List


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

    # 可视化矩形高度（像素）- 替代hard code: 3
    vis_rectangle_height: int = 3

    # 可视化矩形底部偏移（像素）- 替代hard code: 4
    vis_rectangle_bottom_offset: int = 4

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
            'vis_rectangle_height': self.vis_rectangle_height,
            'vis_rectangle_bottom_offset': self.vis_rectangle_bottom_offset,
        }


@dataclass
class SmallImageFilterRules:
    """小图筛选规则配置"""

    # ========== 尺寸规则 ==========
    # 最小图片宽度（像素）
    min_image_width: int = 100

    # 最小图片高度（像素）
    min_image_height: int = 100

    # 最小文件大小（字节）
    min_file_size_bytes: int = 1024

    # ========== 质量规则 ==========
    # 是否检查图片质量
    check_quality: bool = True

    # 最小质量分数（0-100）
    min_quality_score: float = 60.0

    # 是否检查图片模糊度
    check_blur: bool = False

    # 最大模糊度阈值
    max_blur_threshold: float = 100.0

    # ========== 过滤规则 ==========
    # 是否启用自动过滤
    enable_auto_filter: bool = True

    # 是否记录被过滤的图片
    log_filtered_images: bool = True

    # 是否保存被过滤的图片到单独目录
    save_filtered_images: bool = False

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'SmallImageFilterRules':
        """
        从配置字典创建SmallImageFilterRules对象

        Args:
            conf: 配置字典，包含小图筛选规则参数

        Returns:
            SmallImageFilterRules: 小图筛选规则对象
        """
        return cls(**{k: v for k, v in conf.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """
        将SmallImageFilterRules对象转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'min_image_width': self.min_image_width,
            'min_image_height': self.min_image_height,
            'min_file_size_bytes': self.min_file_size_bytes,
            'check_quality': self.check_quality,
            'min_quality_score': self.min_quality_score,
            'check_blur': self.check_blur,
            'max_blur_threshold': self.max_blur_threshold,
            'enable_auto_filter': self.enable_auto_filter,
            'log_filtered_images': self.log_filtered_images,
            'save_filtered_images': self.save_filtered_images,
        }


@dataclass
class VerticalStitchRules:
    """纵图拼接规则配置"""

    # ========== 拼接规则 ==========
    # 输出目录后缀 - 替代hard code: "_vertical"
    output_dir_suffix: str = "_vertical"

    # 默认拼接次数
    default_stitch_count: int = 2

    # 最大拼接次数
    max_stitch_count: int = 5

    # 目标分辨率（宽度）
    target_resolution_width: int = 1024

    # ========== 对齐规则 ==========
    # 是否启用对齐检查
    enable_alignment_check: bool = True

    # 对齐容差（像素）
    alignment_tolerance: int = 10

    # 是否自动调整对齐
    auto_adjust_alignment: bool = False

    # ========== 质量规则 ==========
    # 是否检查拼接质量
    check_stitch_quality: bool = True

    # 最小质量分数（0-100）
    min_stitch_quality: float = 70.0

    # 是否启用拼接后处理
    enable_post_processing: bool = False

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'VerticalStitchRules':
        """
        从配置字典创建VerticalStitchRules对象

        Args:
            conf: 配置字典，包含纵图拼接规则参数

        Returns:
            VerticalStitchRules: 纵图拼接规则对象
        """
        return cls(**{k: v for k, v in conf.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """
        将VerticalStitchRules对象转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'output_dir_suffix': self.output_dir_suffix,
            'default_stitch_count': self.default_stitch_count,
            'max_stitch_count': self.max_stitch_count,
            'target_resolution_width': self.target_resolution_width,
            'enable_alignment_check': self.enable_alignment_check,
            'alignment_tolerance': self.alignment_tolerance,
            'auto_adjust_alignment': self.auto_adjust_alignment,
            'check_stitch_quality': self.check_stitch_quality,
            'min_stitch_quality': self.min_stitch_quality,
            'enable_post_processing': self.enable_post_processing,
        }


@dataclass
class HorizontalStitchRules:
    """横图拼接规则配置"""

    # ========== 拼接规则 ==========
    # 输出目录后缀
    output_dir_suffix: str = "_horizontal"

    # 默认拼接次数
    default_stitch_count: int = 2

    # 最大拼接次数
    max_stitch_count: int = 10

    # 目标分辨率（高度）
    target_resolution_height: int = 1024

    # ========== 对齐规则 ==========
    # 是否启用对齐检查
    enable_alignment_check: bool = True

    # 对齐容差（像素）
    alignment_tolerance: int = 10

    # 是否自动调整对齐
    auto_adjust_alignment: bool = False

    # ========== 质量规则 ==========
    # 是否检查拼接质量
    check_stitch_quality: bool = True

    # 最小质量分数（0-100）
    min_stitch_quality: float = 70.0

    # 是否启用拼接后处理
    enable_post_processing: bool = False

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'HorizontalStitchRules':
        """
        从配置字典创建HorizontalStitchRules对象

        Args:
            conf: 配置字典，包含横图拼接规则参数

        Returns:
            HorizontalStitchRules: 横图拼接规则对象
        """
        return cls(**{k: v for k, v in conf.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """
        将HorizontalStitchRules对象转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'output_dir_suffix': self.output_dir_suffix,
            'default_stitch_count': self.default_stitch_count,
            'max_stitch_count': self.max_stitch_count,
            'target_resolution_height': self.target_resolution_height,
            'enable_alignment_check': self.enable_alignment_check,
            'alignment_tolerance': self.alignment_tolerance,
            'auto_adjust_alignment': self.auto_adjust_alignment,
            'check_stitch_quality': self.check_stitch_quality,
            'min_stitch_quality': self.min_stitch_quality,
            'enable_post_processing': self.enable_post_processing,
        }


@dataclass
class ScoringRules:
    """评分规则配置"""

    # ========== 评分权重 ==========
    # 图案连续性评分权重
    pattern_continuity_weight: float = 1.0

    # 小图筛选评分权重
    small_image_filter_weight: float = 1.0

    # 纵图拼接评分权重
    vertical_stitch_weight: float = 1.0

    # 横图拼接评分权重
    horizontal_stitch_weight: float = 1.0

    # ========== 评分规则 ==========
    # 是否启用详细评分
    enable_detailed_scoring: bool = True

    # 是否记录评分详情
    log_score_details: bool = True

    # 最低及格分数
    minimum_passing_score: int = 60

    # 满分
    maximum_score: int = 100

    # ========== 奖惩规则 ==========
    # 是否启用奖励机制
    enable_bonus_scoring: bool = False

    # 奖励分数上限
    maximum_bonus_score: int = 10

    # 是否启用惩罚机制
    enable_penalty_scoring: bool = True

    # 惩罚分数下限
    maximum_penalty_score: int = -20

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'ScoringRules':
        """
        从配置字典创建ScoringRules对象

        Args:
            conf: 配置字典，包含评分规则参数

        Returns:
            ScoringRules: 评分规则对象
        """
        return cls(**{k: v for k, v in conf.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """
        将ScoringRules对象转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'pattern_continuity_weight': self.pattern_continuity_weight,
            'small_image_filter_weight': self.small_image_filter_weight,
            'vertical_stitch_weight': self.vertical_stitch_weight,
            'horizontal_stitch_weight': self.horizontal_stitch_weight,
            'enable_detailed_scoring': self.enable_detailed_scoring,
            'log_score_details': self.log_score_details,
            'minimum_passing_score': self.minimum_passing_score,
            'maximum_score': self.maximum_score,
            'enable_bonus_scoring': self.enable_bonus_scoring,
            'maximum_bonus_score': self.maximum_bonus_score,
            'enable_penalty_scoring': self.enable_penalty_scoring,
            'maximum_penalty_score': self.maximum_penalty_score,
        }


@dataclass
class TransverseGroovesConfig:
    """横沟检测配置（需求8 & 需求14）"""

    # 各小图类型的最小横沟厚度（mm）
    # center → RIB1/5 以 3.5mm 计算；side → RIB2/3/4 以 1.8mm 计算
    groove_width_mm: Dict[str, float] = field(
        default_factory=lambda: {"center": 3.5, "side": 1.8}
    )

    # 像素密度（px/mm）
    pixel_per_mm: float = 7.1

    # 需求14：允许的最大交叉点数量
    max_intersections: int = 2

    # 需求8满分（横沟数量合规）
    score_groove_count: int = 4

    # 需求14满分（交叉点数量合规）
    score_intersection: int = 2

    # image_type → RIB 标签（用于合规判定分支）
    rib_label: Dict[str, str] = field(
        default_factory=lambda: {"center": "RIB1/5", "side": "RIB2/3/4"}
    )

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'TransverseGroovesConfig':
        """从配置字典创建对象"""
        return cls(**{k: v for k, v in conf.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'groove_width_mm':    dict(self.groove_width_mm),
            'pixel_per_mm':       self.pixel_per_mm,
            'max_intersections':  self.max_intersections,
            'score_groove_count': self.score_groove_count,
            'score_intersection': self.score_intersection,
            'rib_label':          dict(self.rib_label),
        }


@dataclass
class BusinessRules:
    """业务规则汇总配置，整合所有规则配置"""

    # 图案连续性检测规则
    pattern_continuity: PatternContinuityConfig = field(default_factory=PatternContinuityConfig)

    # 横沟检测规则
    transverse_grooves: TransverseGroovesConfig = field(default_factory=TransverseGroovesConfig)

    # 小图筛选规则
    small_image_filter: SmallImageFilterRules = field(default_factory=SmallImageFilterRules)

    # 纵图拼接规则
    vertical_stitch: VerticalStitchRules = field(default_factory=VerticalStitchRules)

    # 横图拼接规则
    horizontal_stitch: HorizontalStitchRules = field(default_factory=HorizontalStitchRules)

    # 评分规则
    scoring: ScoringRules = field(default_factory=ScoringRules)

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'BusinessRules':
        """
        从配置字典创建BusinessRules对象

        Args:
            conf: 配置字典，包含业务规则参数

        Returns:
            BusinessRules: 业务规则对象
        """
        return cls(
            pattern_continuity=PatternContinuityConfig.from_dict(
                conf.get('pattern_continuity', {})
            ),
            transverse_grooves=TransverseGroovesConfig.from_dict(
                conf.get('transverse_grooves', {})
            ),
            small_image_filter=SmallImageFilterRules.from_dict(
                conf.get('small_image_filter', {})
            ),
            vertical_stitch=VerticalStitchRules.from_dict(
                conf.get('vertical_stitch', {})
            ),
            horizontal_stitch=HorizontalStitchRules.from_dict(
                conf.get('horizontal_stitch', {})
            ),
            scoring=ScoringRules.from_dict(
                conf.get('scoring', {})
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        将BusinessRules对象转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'pattern_continuity': self.pattern_continuity.to_dict(),
            'transverse_grooves': self.transverse_grooves.to_dict(),
            'small_image_filter': self.small_image_filter.to_dict(),
            'vertical_stitch': self.vertical_stitch.to_dict(),
            'horizontal_stitch': self.horizontal_stitch.to_dict(),
            'scoring': self.scoring.to_dict(),
        }
