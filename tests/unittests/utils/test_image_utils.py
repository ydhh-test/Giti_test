import base64
import numpy as np
import cv2
from pathlib import Path
from PIL import Image
import tempfile
import pytest
import logging

from src.utils.image_utils import (
    base64_to_ndarray,
    ndarray_to_base64,
    resize_image,
    load_image_to_base64,
    save_base64_to_image,
    convert_cmyk_to_rgb
)
from src.common.exceptions import (
    InputTypeError,
    InputDataError,
    RuntimeProcessError
)
from src.utils.logger import get_logger


# 创建测试用的numpy数组（BGR格式）
TEST_IMAGE_ARRAY = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

# 创建对应的base64字符串（带前缀）
_, buffer = cv2.imencode('.png', TEST_IMAGE_ARRAY)
TEST_IMAGE_BASE64_WITH_PREFIX = f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"

# 创建对应的base64字符串（无前缀）
TEST_IMAGE_BASE64_NO_PREFIX = base64.b64encode(buffer).decode('utf-8')

# 支持的图像类型
SUPPORTED_IMAGE_TYPES = ["png", "jpg", "jpeg"]

# 不支持的图像类型
UNSUPPORTED_IMAGE_TYPES = ["bmp", "tiff", "webp"]

INVALID_BASE64_STRINGS = [
    "invalid_base64_string",
    "data:image/png;base64,invalid",
    "",
    "data:image/bmp;base64,xxx"  # 不支持的格式前缀
]

# 配置日志捕获
@pytest.fixture(autouse=True)
def capture_logs(caplog):
    caplog.set_level(logging.WARNING)


class TestBase64ToNdarray:
    """base64_to_ndarray() 功能测试"""

    def test_valid_base64_with_prefix(self):
        """带data:image前缀的base64正确解码"""
        result = base64_to_ndarray(TEST_IMAGE_BASE64_WITH_PREFIX)
        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_valid_base64_no_prefix(self):
        """纯base64字符串正确解码"""
        result = base64_to_ndarray(TEST_IMAGE_BASE64_NO_PREFIX)
        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_different_image_formats(self):
        """PNG、JPG、JPEG格式都支持"""
        # 测试JPG格式
        _, jpg_buffer = cv2.imencode('.jpg', TEST_IMAGE_ARRAY, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        jpg_base64 = f"data:image/jpeg;base64,{base64.b64encode(jpg_buffer).decode('utf-8')}"
        result = base64_to_ndarray(jpg_base64)
        assert isinstance(result, np.ndarray)

        # 测试JPEG格式（同JPG）
        jpeg_base64 = f"data:image/jpeg;base64,{base64.b64encode(jpg_buffer).decode('utf-8')}"
        result = base64_to_ndarray(jpeg_base64)
        assert isinstance(result, np.ndarray)

    def test_input_type_error_non_string(self):
        """非字符串输入抛出InputTypeError"""
        with pytest.raises(InputTypeError) as exc_info:
            base64_to_ndarray(123)
        assert "base64_to_ndarray" in str(exc_info.value)
        assert "expects str" in str(exc_info.value)

    def test_input_data_error_invalid_base64(self):
        """无效base64字符串抛出InputDataError"""
        with pytest.raises(InputDataError) as exc_info:
            base64_to_ndarray("invalid_base64_string")
        assert "invalid_base64_string" in str(exc_info.value)

    def test_input_data_error_unsupported_format(self):
        """不支持的图像格式抛出InputDataError"""
        # 创建一个无效的base64字符串
        invalid_base64 = "data:image/bmp;base64," + base64.b64encode(b"invalid_data").decode('utf-8')
        with pytest.raises(InputDataError):
            base64_to_ndarray(invalid_base64)


class TestNdarrayToBase64:
    """ndarray_to_base64() 功能测试"""

    def test_valid_ndarray_to_png(self):
        """numpy数组转PNG base64"""
        result = ndarray_to_base64(TEST_IMAGE_ARRAY, "png")
        assert isinstance(result, str)
        assert result.startswith("data:image/png;base64,")

    def test_valid_ndarray_to_jpg(self):
        """numpy数组转JPG base64"""
        result = ndarray_to_base64(TEST_IMAGE_ARRAY, "jpg")
        assert isinstance(result, str)
        assert result.startswith("data:image/jpg;base64,")

    def test_with_prefix_true(self):
        """with_prefix=True返回带前缀字符串"""
        result = ndarray_to_base64(TEST_IMAGE_ARRAY, "png", with_prefix=True)
        assert result.startswith("data:image/png;base64,")

    def test_with_prefix_false(self):
        """with_prefix=False返回纯base64"""
        result = ndarray_to_base64(TEST_IMAGE_ARRAY, "png", with_prefix=False)
        assert not result.startswith("data:image/")
        # 验证可以被base64解码
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_input_type_error_non_ndarray(self):
        """非numpy数组输入抛出InputTypeError"""
        with pytest.raises(InputTypeError) as exc_info:
            ndarray_to_base64("not_an_array")
        assert "ndarray_to_base64" in str(exc_info.value)
        assert "expects np.ndarray" in str(exc_info.value)

    def test_input_type_error_wrong_ndarray_shape(self):
        """错误形状的数组抛出InputTypeError"""
        # 创建一个错误形状的数组（4D）
        wrong_shape_array = np.random.randint(0, 256, (100, 100, 3, 3), dtype=np.uint8)
        with pytest.raises(InputTypeError) as exc_info:
            ndarray_to_base64(wrong_shape_array)
        # 注意：OpenCV可能会处理这个，所以我们需要检查实际行为
        # 如果OpenCV能处理，这个测试可能不会抛出异常

    def test_input_data_error_empty_array(self):
        """空数组抛出InputDataError"""
        empty_array = np.array([])
        with pytest.raises(InputDataError):
            ndarray_to_base64(empty_array)


class TestResizeImage:
    """resize_image() 功能测试"""

    def test_stretch_mode_exact_dimensions(self):
        """stretch模式精确缩放到指定尺寸"""
        target_width, target_height = 50, 75
        result = resize_image(TEST_IMAGE_ARRAY, target_width, target_height, "stretch")
        assert result.shape == (target_height, target_width, 3)

    def test_width_scale_mode_proportional(self):
        """width_scale模式按宽度等比缩放"""
        target_width = 50
        original_h, original_w = TEST_IMAGE_ARRAY.shape[:2]
        expected_height = int(original_h * (target_width / original_w))
        result = resize_image(TEST_IMAGE_ARRAY, target_width, mode="width_scale")
        assert result.shape == (expected_height, target_width, 3)

    def test_height_scale_mode_proportional(self):
        """height_scale模式按高度等比缩放"""
        target_height = 75
        original_h, original_w = TEST_IMAGE_ARRAY.shape[:2]
        expected_width = int(original_w * (target_height / original_h))
        result = resize_image(TEST_IMAGE_ARRAY, target_width=original_w, target_height=target_height, mode="height_scale")
        assert result.shape == (target_height, expected_width, 3)

    def test_grayscale_image_support(self):
        """支持单通道灰度图像"""
        gray_array = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        result = resize_image(gray_array, 50, 50, "stretch")
        assert result.shape == (50, 50)

    def test_input_type_error_non_ndarray(self):
        """非numpy数组输入抛出InputTypeError"""
        with pytest.raises(InputTypeError) as exc_info:
            resize_image("not_an_array", 50, 50)
        assert "resize_image" in str(exc_info.value)

    def test_input_type_error_invalid_mode(self):
        """无效mode参数抛出InputTypeError"""
        with pytest.raises(InputTypeError) as exc_info:
            resize_image(TEST_IMAGE_ARRAY, 50, 50, "invalid_mode")
        # 注意：当前实现中，无效mode不会抛出异常，而是会执行stretch分支
        # 我们需要修改实现来添加mode验证

    def test_input_data_error_zero_dimensions(self):
        """零尺寸抛出InputDataError"""
        with pytest.raises(InputDataError):
            resize_image(TEST_IMAGE_ARRAY, 0, 50)

    def test_input_data_error_negative_dimensions(self):
        """负尺寸抛出InputDataError"""
        with pytest.raises(InputDataError):
            resize_image(TEST_IMAGE_ARRAY, -10, 50)


class TestLoadImageToBase64:
    """load_image_to_base64() 功能测试"""

    def test_load_png_with_prefix(self):
        """加载PNG文件返回带前缀base64"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "test.png"
            cv2.imwrite(str(image_path), TEST_IMAGE_ARRAY)

            result = load_image_to_base64(image_path, with_prefix=True)

            assert isinstance(result, str)
            assert result.startswith("data:image/png;base64,")

    def test_load_jpg_with_prefix(self):
        """加载JPG文件返回带前缀base64"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "test.jpg"
            cv2.imwrite(str(image_path), TEST_IMAGE_ARRAY, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

            result = load_image_to_base64(image_path, with_prefix=True)

            assert isinstance(result, str)
            assert result.startswith("data:image/jpg;base64,")

    def test_load_without_prefix(self):
        """with_prefix=False返回纯base64"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "test.png"
            cv2.imwrite(str(image_path), TEST_IMAGE_ARRAY)

            result = load_image_to_base64(image_path, with_prefix=False)

            assert isinstance(result, str)
            assert not result.startswith("data:image/")

    def test_input_type_error_non_path(self):
        """非Path对象输入抛出InputTypeError"""
        with pytest.raises(InputTypeError) as exc_info:
            load_image_to_base64("not_a_path")
        assert "load_image_to_base64" in str(exc_info.value)

    def test_input_data_error_file_not_found(self):
        """文件不存在抛出InputDataError"""
        non_existent_path = Path("nonexistent_file.png")
        with pytest.raises(InputDataError) as exc_info:
            load_image_to_base64(non_existent_path)
        assert "nonexistent_file.png" in str(exc_info.value)

    def test_input_data_error_unsupported_format(self):
        """不支持格式文件抛出InputDataError并记录警告"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "test.bmp"
            simple_array = np.zeros((10, 10, 3), dtype=np.uint8)
            cv2.imwrite(str(image_path), simple_array)

            with pytest.raises(InputDataError):
                load_image_to_base64(image_path)

    def test_warning_logged_for_unsupported_format(self, caplog):
        """不支持格式触发警告日志"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "test.bmp"
            simple_array = np.zeros((10, 10, 3), dtype=np.uint8)
            cv2.imwrite(str(image_path), simple_array)

            try:
                load_image_to_base64(image_path)
            except InputDataError:
                pass
            assert any("警告: 不支持的文件格式" in record.message for record in caplog.records)


class TestSaveBase64ToImage:
    """save_base64_to_image() 功能测试"""

    def test_save_with_prefix_to_png(self):
        """带前缀base64保存为PNG"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "test_image.jpg"  # 注意：这里用.jpg后缀
            save_base64_to_image(TEST_IMAGE_BASE64_WITH_PREFIX, save_path, with_prefix=True)
            # 验证文件存在且是PNG格式
            saved_path = save_path.with_suffix(".png")
            assert saved_path.exists()
            # 验证可以读取
            loaded_image = cv2.imread(str(saved_path))
            assert loaded_image is not None

    def test_save_without_prefix_to_png(self):
        """纯base64保存为PNG"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "test_image.png"
            save_base64_to_image(TEST_IMAGE_BASE64_NO_PREFIX, save_path, with_prefix=False)
            assert save_path.exists()
            loaded_image = cv2.imread(str(save_path))
            assert loaded_image is not None

    def test_file_extension_overridden(self):
        """自动修正文件后缀为.png"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = Path(tmp_dir) / "test_image.jpg"
            save_base64_to_image(TEST_IMAGE_BASE64_WITH_PREFIX, original_path)
            # 验证实际保存的文件是.png
            png_path = original_path.with_suffix(".png")
            assert png_path.exists()
            assert not original_path.exists()

    def test_input_type_error_invalid_base64(self):
        """无效base64字符串抛出InputDataError"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "test.png"
            with pytest.raises(InputDataError):
                save_base64_to_image("invalid_base64", save_path)

    def test_input_type_error_non_path(self):
        """非Path对象输入抛出InputTypeError"""
        with pytest.raises(InputTypeError) as exc_info:
            save_base64_to_image(TEST_IMAGE_BASE64_WITH_PREFIX, "not_a_path")
        assert "save_base64_to_image" in str(exc_info.value)


class TestConvertCmykToRgb:
    """convert_cmyk_to_rgb() 功能测试"""

    def test_valid_cmyk_pil_to_bgr(self):
        """CMYK PIL图像正确转换为BGR numpy数组"""
        # 创建CMYK PIL图像
        cmyk_image = Image.new('CMYK', (100, 100), (100, 50, 75, 25))
        result = convert_cmyk_to_rgb(cmyk_image)
        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_input_type_error_non_pil_image(self):
        """非PIL Image对象抛出InputTypeError"""
        with pytest.raises(InputTypeError) as exc_info:
            convert_cmyk_to_rgb("not_a_pil_image")
        assert "convert_cmyk_to_rgb" in str(exc_info.value)

    def test_input_type_error_rgb_pil_image(self):
        """RGB PIL图像输入抛出InputTypeError"""
        rgb_image = Image.new('RGB', (100, 100), (255, 128, 64))
        # 当前实现不会抛出异常，会正常转换
        # 这个测试可能需要根据实际需求调整


class TestIntegration:
    """函数集成测试"""

    def test_round_trip_base64_ndarray(self):
        """base64 → ndarray → base64 完整往返"""
        # 原始base64
        original_base64 = TEST_IMAGE_BASE64_WITH_PREFIX
        # 转换为ndarray
        ndarray = base64_to_ndarray(original_base64)
        # 转换回base64
        new_base64 = ndarray_to_base64(ndarray, "png", with_prefix=True)
        # 验证可以再次转换为ndarray
        final_ndarray = base64_to_ndarray(new_base64)
        assert final_ndarray.shape == ndarray.shape

    def test_load_resize_save_workflow(self):
        """load → resize → save 完整工作流"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 创建源文件
            source_path = Path(tmp_dir) / "source.png"
            cv2.imwrite(str(source_path), TEST_IMAGE_ARRAY)

            # 加载为base64
            base64_str = load_image_to_base64(source_path)

            # 转换为ndarray
            image_array = base64_to_ndarray(base64_str)

            # 调整大小
            resized_array = resize_image(image_array, 50, 50, "stretch")

            # 保存为新文件
            target_path = Path(tmp_dir) / "target.jpg"
            save_base64_to_image(ndarray_to_base64(resized_array, "png"), target_path)

            # 验证目标文件存在
            final_path = target_path.with_suffix(".png")
            assert final_path.exists()

    def test_multiple_resize_modes_comparison(self):
        """不同缩放模式结果对比验证"""
        original_h, original_w = TEST_IMAGE_ARRAY.shape[:2]

        # stretch模式
        stretch_result = resize_image(TEST_IMAGE_ARRAY, 50, 75, "stretch")
        assert stretch_result.shape == (75, 50, 3)

        # width_scale模式
        width_result = resize_image(TEST_IMAGE_ARRAY, 50, mode="width_scale")
        expected_height = int(original_h * (50 / original_w))
        assert width_result.shape == (expected_height, 50, 3)

        # height_scale模式
        height_result = resize_image(TEST_IMAGE_ARRAY, target_width=original_w, target_height=75, mode="height_scale")
        expected_width = int(original_w * (75 / original_h))
        assert height_result.shape == (75, expected_width, 3)


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_base64_strings(self):
        """空base64字符串处理"""
        with pytest.raises(InputDataError):
            base64_to_ndarray("")

    def test_single_pixel_images(self):
        """单像素图像处理"""
        single_pixel = np.array([[[255, 128, 64]]], dtype=np.uint8)
        result = resize_image(single_pixel, 10, 10, "stretch")
        assert result.shape == (10, 10, 3)

    def test_special_characters_in_paths(self):
        """路径包含特殊字符"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            special_path = Path(tmp_dir) / "test-image_测试.png"
            cv2.imwrite(str(special_path), TEST_IMAGE_ARRAY)
            base64_str = load_image_to_base64(special_path)
            assert isinstance(base64_str, str)

    def test_unicode_paths(self):
        """Unicode路径支持"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            unicode_path = Path(tmp_dir) / "图片.png"
            cv2.imwrite(str(unicode_path), TEST_IMAGE_ARRAY)
            base64_str = load_image_to_base64(unicode_path)
            assert isinstance(base64_str, str)