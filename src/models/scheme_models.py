# ============================================================
# 方案模型
#
# 包含：
#   第一部分：拼接模板类（frozen=True）
#     - RibTemplate / StitchingTemplate
#     - Symmetry0 / Symmetry1 / _Concatenate0 / Continuity0
#   第二部分：拼接运行时类（validate_assignment=True）
#     - RibSchemeImpl / StitchingSchemeAbstract / StitchingScheme
#   第三部分：主沟花纹方案
#     - MainGrooveImpl / MainGrooveSchemeAbstract / MainGrooveScheme
#   第四部分：装饰花纹方案
#     - DecorationImpl / DecorationSchemeAbstract / DecorationScheme
#
# 注意：
#   - 模板类必须设置 frozen=True
#   - 运行时类必须开启 validate_assignment=True
# ============================================================

from typing import Optional, List, Tuple
from pydantic import BaseModel, Field, ConfigDict, model_validator

from .enums import RegionEnum, SourceTypeEnum, StitchingSchemeName, RibOperation


# ============================================================
# 第一部分：拼接模板类（frozen=True）
# ============================================================

class RibTemplate(BaseModel):
    """
    RIB模板定义

    只定义操作序列模板，不存运行时数据。

    注意：
    - operation_template 和 sub_template_name 二选一
    - 使用 sub_template_name 时，operation_template 可为空
    """

    model_config = ConfigDict(frozen=True)

    region: Optional[RegionEnum] = Field(default=None, description="来源区域")
    source_type: SourceTypeEnum = Field(default=SourceTypeEnum.ORIGINAL, description="来源类型")
    inherit_from: Optional[str] = Field(default=None, description="继承自哪个rib_name")
    operation_template: Optional[Tuple[RibOperation, ...]] = Field(default=None, description="操作序列模板")
    rib_name: Optional[str] = Field(default=None, description="RIB名称，如rib1，最外层必填")
    sub_template_name: Optional[StitchingSchemeName] = Field(default=None, description="子模板名称")

    @model_validator(mode="after")
    def _validate_operation_or_sub_template(self) -> "RibTemplate":
        """私有校验：operation_template 和 sub_template_name 二选一"""
        has_operation = self.operation_template is not None
        has_sub_template = self.sub_template_name is not None
        if not has_operation and not has_sub_template:
            raise ValueError("operation_template 和 sub_template_name 必须二选一")
        if has_operation and has_sub_template:
            raise ValueError("operation_template 和 sub_template_name 不能同时存在")
        return self


class StitchingTemplate(BaseModel):
    """
    拼接模板基类

    静态配置模板，只定义拼接规则，不存合成图片。
    子类：Symmetry0、Symmetry1、Continuity0、_Concatenate0等。
    """

    model_config = ConfigDict(frozen=True)

    name: StitchingSchemeName = Field(description="拼接方案名称枚举")
    description: str = Field(description="方案描述")
    rib_number: int = Field(description="RIB数量")
    mode: str = Field(description="模式")
    rib_template_list: List[RibTemplate] = Field(description="RIB模板定义列表")
    post_processing: Optional[Tuple[RibOperation, ...]] = Field(default=None, description="后处理操作序列")


class Symmetry0(StitchingTemplate):
    """拼接模板：symmetry_0 - 5个花纹RIB无对称原则"""

    name: StitchingSchemeName = StitchingSchemeName.SYMMETRY_0
    description: str = "花纹RIB无对称原则"
    rib_number: int = 5
    mode: str = "symmetry"
    rib_template_list: List[RibTemplate] = [
        RibTemplate(region=RegionEnum.SIDE, operation_template=(RibOperation.NONE,), rib_name="rib1"),
        RibTemplate(region=RegionEnum.CENTER, operation_template=(RibOperation.NONE,), rib_name="rib2"),
        RibTemplate(region=RegionEnum.CENTER, operation_template=(RibOperation.NONE,), rib_name="rib3"),
        RibTemplate(region=RegionEnum.CENTER, operation_template=(RibOperation.NONE,), rib_name="rib4"),
        RibTemplate(region=RegionEnum.SIDE, operation_template=(RibOperation.NONE,), rib_name="rib5"),
    ]


class Symmetry1(StitchingTemplate):
    """拼接模板：symmetry_1 - 花纹RIB中心对称（左侧旋转180度是右侧）"""

    name: StitchingSchemeName = StitchingSchemeName.SYMMETRY_1
    description: str = "花纹RIB中心对称（左侧旋转180度是右侧）"
    rib_number: int = 5
    mode: str = "symmetry"
    rib_template_list: List[RibTemplate] = [
        RibTemplate(region=RegionEnum.SIDE, operation_template=(RibOperation.NONE,), rib_name="rib1"),
        RibTemplate(region=RegionEnum.CENTER, operation_template=(RibOperation.NONE,), rib_name="rib2"),
        RibTemplate(region=RegionEnum.CENTER, operation_template=(RibOperation.LEFT_FLIP,), rib_name="rib3"),
        RibTemplate(region=RegionEnum.CENTER, source_type=SourceTypeEnum.INHERIT, inherit_from="rib2",
                    operation_template=(RibOperation.FLIP,), rib_name="rib4"),
        RibTemplate(region=RegionEnum.SIDE, source_type=SourceTypeEnum.INHERIT, inherit_from="rib1",
                    operation_template=(RibOperation.FLIP,), rib_name="rib5"),
    ]


class _Concatenate0(StitchingTemplate):
    """拼接模板：_concatenate_0 - 用于两张图像的拼接（供内部使用）"""

    name: StitchingSchemeName = StitchingSchemeName._CONCATENATE_0
    description: str = "两张图合并为1张，仅供内部使用"
    rib_number: int = 2
    mode: str = "concatenate"
    rib_template_list: List[RibTemplate] = [
        RibTemplate(source_type=SourceTypeEnum.INHERIT, inherit_from="rib2",
                    operation_template=(RibOperation.RESIZE_HORIZONTAL_3X, RibOperation.RIGHT_1_3)),
        RibTemplate(source_type=SourceTypeEnum.INHERIT, inherit_from="rib2",
                    operation_template=(RibOperation.RESIZE_HORIZONTAL_3X, RibOperation.LEFT_1_3)),
    ]
    post_processing: Tuple[RibOperation, ...] = (RibOperation._RESIZE_AS_FIRST_RIB,)


class Continuity0(StitchingTemplate):
    """拼接模板：continuity_0 - RIB2-RIB3-RIB4中间三条全连续，边缘独立"""

    name: StitchingSchemeName = StitchingSchemeName.CONTINUITY_0
    description: str = "RIB2-RIB3-RIB4中间全连续，边缘独立"
    rib_number: int = 5
    mode: str = "continuity"
    rib_template_list: List[RibTemplate] = [
        RibTemplate(source_type=SourceTypeEnum.INHERIT, inherit_from="rib1",
                    operation_template=(RibOperation.NONE,), rib_name="rib1"),
        RibTemplate(source_type=SourceTypeEnum.INHERIT, inherit_from="rib2",
                    operation_template=(RibOperation.RESIZE_HORIZONTAL_1_5X, RibOperation.LEFT_2_3), rib_name="rib2"),
        RibTemplate(sub_template_name=StitchingSchemeName._CONCATENATE_0, rib_name="rib3"),
        RibTemplate(source_type=SourceTypeEnum.INHERIT, inherit_from="rib4",
                    operation_template=(RibOperation.RESIZE_HORIZONTAL_1_5X, RibOperation.RIGHT_2_3), rib_name="rib4"),
        RibTemplate(source_type=SourceTypeEnum.INHERIT, inherit_from="rib5",
                    operation_template=(RibOperation.NONE,), rib_name="rib5"),
    ]


# ============================================================
# 第二部分：拼接运行时类（validate_assignment=True）
# ============================================================

class RibSchemeImpl(BaseModel):
    """
    RIB拼接方案实现实体（运行时）

    由TemplateInstantiator从StitchingTemplate实例化而来。
    包含操作序列、执行结果图片、节距数等运行时信息。
    """

    model_config = ConfigDict(validate_assignment=True)

    region: Optional[RegionEnum] = Field(default=None, description="来源区域")
    source_type: SourceTypeEnum = Field(description="来源类型")
    inherit_from: Optional[str] = Field(default=None, description="继承自哪个rib_name")
    operations: Tuple[RibOperation, ...] = Field(description="操作序列")
    rib_name: Optional[str] = Field(default=None, description="RIB名称")
    is_nested: bool = Field(default=False, description="是否嵌套RIB")

    # ---- 运行时填充字段 ----
    small_image: Optional[str] = Field(default=None, description="小图base64")
    num_pitchs: Optional[int] = Field(default=None, description="节距数量")
    rib_height: Optional[int] = Field(default=None, description="RIB纵向图高度")
    rib_width: Optional[int] = Field(default=None, description="RIB纵向图宽度")
    rib_image: Optional[str] = Field(default=None, description="操作后的纵向图base64")

    @model_validator(mode="after")
    def _validate_name_required_for_top_level(self) -> "RibSchemeImpl":
        """私有校验：最外层RIB必须有名称"""
        if not self.is_nested and self.rib_name is None:
            raise ValueError("最外层RIB必须有rib_name")
        return self

    @model_validator(mode="after")
    def _validate_inherit_has_reference(self) -> "RibSchemeImpl":
        """私有校验：继承来源必须有inherit_from"""
        if self.source_type == SourceTypeEnum.INHERIT and self.inherit_from is None:
            raise ValueError("继承来源必须指定inherit_from")
        return self


class StitchingSchemeAbstract(BaseModel):
    """拼接方案摘要 - 人类可读的方案描述信息"""

    name: StitchingSchemeName = Field(description="方案名称枚举")
    description: str = Field(description="方案描述")
    rib_number: int = Field(description="RIB数量")


class StitchingScheme(BaseModel):
    """
    大图拼接完整方案（运行时）

    由TemplateInstantiator生成，存储实际执行数据和结果。
    """

    stitching_scheme_abstract: StitchingSchemeAbstract = Field(description="拼接方案摘要")
    ribs_scheme_implementation: List[RibSchemeImpl] = Field(default_factory=list, description="RIB拼接方案实现列表")


# ============================================================
# 第三部分：主沟花纹方案
# ============================================================

class MainGrooveImpl(BaseModel):
    """主沟花纹实现实体（程序使用）- 存储主沟的图像数据和尺寸信息"""

    groove_image: Optional[str] = Field(default=None, description="主沟图base64")
    groove_width: int = Field(description="主沟宽度(像素)")
    groove_height: int = Field(description="主沟高度(像素)")


class MainGrooveSchemeAbstract(BaseModel):
    """主沟方案摘要（给人看）"""

    name: str = Field(description="方案名称")
    description: Optional[str] = Field(default=None, description="方案描述")
    groove_number: int = Field(description="主沟数量")


class MainGrooveScheme(BaseModel):
    """主沟花纹完整方案 - 包含方案摘要和实现列表"""

    main_groove_scheme_abstract: Optional[MainGrooveSchemeAbstract] = Field(default=None, description="主沟方案摘要")
    main_groove_implementation: List[MainGrooveImpl] = Field(default_factory=list, description="主沟实现列表")


# ============================================================
# 第四部分：装饰花纹方案
# ============================================================

class DecorationImpl(BaseModel):
    """装饰花纹实现实体（程序使用）- 存储装饰花纹的图像数据、尺寸和透明度"""

    decoration_image: Optional[str] = Field(default=None, description="装饰花纹图base64")
    decoration_width: int = Field(description="装饰宽度(像素)")
    decoration_height: int = Field(description="装饰高度(像素)")
    decoration_opacity: int = Field(ge=0, le=255, description="边缘花纹透明度")


class DecorationSchemeAbstract(BaseModel):
    """装饰方案摘要（给人看）"""

    name: str = Field(description="方案名称")
    description: Optional[str] = Field(default=None, description="方案描述")


class DecorationScheme(BaseModel):
    """装饰花纹完整方案 - 包含方案摘要和实现列表"""

    decoration_scheme_abstract: Optional[DecorationSchemeAbstract] = Field(default=None, description="装饰方案摘要")
    decoration_implementation: List[DecorationImpl] = Field(default_factory=list, description="装饰实现列表")