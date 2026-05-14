"""
大图拼接集成测试

使用真实图片验证完整的端到端流程：
5个RIB + 4个主沟 + 黑色半透明装饰覆盖
"""

import base64
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.models.enums import (
    RegionEnum,
    RibOperation,
    SourceTypeEnum,
    StitchingSchemeName,
)
from src.models.image_models import ImageLineage
from src.models.scheme_models import (
    DecorationImpl,
    DecorationScheme,
    DecorationSchemeAbstract,
    MainGrooveImpl,
    MainGrooveScheme,
    MainGrooveSchemeAbstract,
    RibSchemeImpl,
    StitchingScheme,
    StitchingSchemeAbstract,
)
from src.processing.image_stiching import generate_large_image_from_lineage


DATASET_DIR = Path("tests/datasets/stitching")
EXPECTED_PATH = DATASET_DIR / "correct_black_decoration.png"


def _ndarray_to_base64(image: np.ndarray) -> str:
    success, buffer = cv2.imencode(".png", image)
    if not success:
        raise ValueError("Failed to encode image")
    base64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/png;base64,{base64_str}"


def _resize_image(image: np.ndarray, target_width: int, target_height: int) -> np.ndarray:
    return cv2.resize(image, (target_width, target_height))


def _build_lineage_with_black_decoration() -> ImageLineage:
    """
    构建与 correct_black_decoration.png 相同配置的 ImageLineage。

    配置：
    - rib1、rib5: 400×640, 区域 SIDE
    - rib2、rib3、rib4: 200×640, 区域 CENTER
    - num_pitchs = 5
    - 主沟: 4 个, 20×640, 黑色
    - 装饰: 300×640, 纯黑色, 50% 透明度
    """
    target_rib_configs = {
        1: {"width": 400, "height": 640, "region": RegionEnum.SIDE},
        2: {"width": 200, "height": 640, "region": RegionEnum.CENTER},
        3: {"width": 200, "height": 640, "region": RegionEnum.CENTER},
        4: {"width": 200, "height": 640, "region": RegionEnum.CENTER},
        5: {"width": 400, "height": 640, "region": RegionEnum.SIDE},
    }

    ribs_scheme_implementation = []
    for i in range(1, 6):
        config = target_rib_configs[i]
        rib_path = DATASET_DIR / f"rib{i}.png"
        rib_img = cv2.imread(str(rib_path))
        assert rib_img is not None, f"无法加载 {rib_path}"
        resized = _resize_image(rib_img, config["width"], config["height"])

        rib_impl = RibSchemeImpl(
            region=config["region"],
            source_type=SourceTypeEnum.ORIGINAL,
            operations=(RibOperation.NONE,),
            rib_name=f"rib{i}",
            small_image=_ndarray_to_base64(resized),
            num_pitchs=5,
            rib_height=config["height"],
            rib_width=config["width"],
        )
        ribs_scheme_implementation.append(rib_impl)

    stitching_scheme = StitchingScheme(
        stitching_scheme_abstract=StitchingSchemeAbstract(
            name=StitchingSchemeName.SYMMETRY_0,
            description="integration test",
            rib_number=5,
        ),
        ribs_scheme_implementation=ribs_scheme_implementation,
    )

    # 4 个主沟, 20×640, 黑色
    groove_img = np.zeros((640, 20, 3), dtype=np.uint8)
    groove_base64 = _ndarray_to_base64(groove_img)
    main_groove_impls = [
        MainGrooveImpl(groove_image=groove_base64, groove_width=20, groove_height=640)
        for _ in range(4)
    ]
    main_groove_scheme = MainGrooveScheme(
        main_groove_scheme_abstract=MainGrooveSchemeAbstract(name="test", groove_number=4),
        main_groove_implementation=main_groove_impls,
    )

    # 装饰: 300×640, 纯黑色, 50% 透明度
    decoration_img = np.zeros((640, 300, 3), dtype=np.uint8)
    decoration_base64 = _ndarray_to_base64(decoration_img)
    decoration_impl = DecorationImpl(
        decoration_image=decoration_base64,
        decoration_width=300,
        decoration_height=640,
        decoration_opacity=128,
    )
    decoration_scheme = DecorationScheme(
        decoration_scheme_abstract=DecorationSchemeAbstract(name="test"),
        decoration_implementation=[decoration_impl],
    )

    return ImageLineage(
        stitching_scheme=stitching_scheme,
        main_groove_scheme=main_groove_scheme,
        decoration_scheme=decoration_scheme,
    )


class TestLargeImageStitchingIntegration:
    """大图拼接端到端集成测试"""

    @pytest.fixture(scope="class")
    def expected_image(self) -> np.ndarray:
        expected = cv2.imread(str(EXPECTED_PATH))
        if expected is None:
            pytest.fail(f"预期结果文件不存在: {EXPECTED_PATH}")
        return expected

    def test_generates_same_result_as_expected(self, expected_image):
        """验证生成的完整大图与预期结果完全一致"""
        lineage = _build_lineage_with_black_decoration()
        result_lineage, result_base64 = generate_large_image_from_lineage(lineage)

        assert result_base64.startswith("data:image/"), "输出应为 data:image 前缀的 base64"

        # 解码结果图像
        b64data = result_base64.split(",")[1]
        img_array = np.frombuffer(base64.b64decode(b64data), dtype=np.uint8)
        actual = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        assert actual is not None, "解码生成的大图失败"
        assert actual.shape == expected_image.shape, (
            f"尺寸不匹配: 实际 {actual.shape}, 预期 {expected_image.shape}"
        )

        np.testing.assert_array_equal(actual, expected_image)

    def test_output_size_matches_ribs_and_grooves(self):
        """验证输出尺寸 = RIB总宽 + 主沟总宽（装饰不扩展尺寸）"""
        lineage = _build_lineage_with_black_decoration()
        _, result_base64 = generate_large_image_from_lineage(lineage)

        b64data = result_base64.split(",")[1]
        img_array = np.frombuffer(base64.b64decode(b64data), dtype=np.uint8)
        actual = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        expected_width = 400 + 200 + 200 + 200 + 400 + 20 * 4  # 1480
        expected_height = 640
        assert actual.shape == (expected_height, expected_width, 3)

    def test_decoration_makes_white_background_darker(self):
        """验证黑色半透明装饰使白色背景区域变暗"""
        lineage = _build_lineage_with_black_decoration()
        _, result_base64 = generate_large_image_from_lineage(lineage)

        b64data = result_base64.split(",")[1]
        img_array = np.frombuffer(base64.b64decode(b64data), dtype=np.uint8)
        actual = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        # 原始 RIB 背景约为 214, 黑色装饰 0 + 50% → 约 107
        left_region = actual[:, :300]
        left_mean = float(np.mean(left_region))
        assert left_mean > 50, "左侧不应全黑"
        assert left_mean < 160, f"左侧应因黑色装饰变暗，实际均值 {left_mean}"
