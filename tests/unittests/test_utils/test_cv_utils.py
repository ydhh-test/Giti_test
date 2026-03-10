# -*- coding: utf-8 -*-

"""
cv_utils模块单元测试
"""


import pytest
import numpy as np
import cv2
from pathlib import Path
from utils.cv_utils import add_gray_borders


class TestAddGrayBorders:
    """测试add_gray_borders函数"""

    @pytest.fixture
    def sample_image(self):
        """创建测试用的样本图像（1200x800，纯白色）"""
        return np.ones((800, 1200, 3), dtype=np.uint8) * 255

    @pytest.fixture
    def default_conf(self):
        """默认配置"""
        return {
            'tire_design_width': 700,
            'decoration_border_alpha': 0.5,
            'decoration_gray_color': (135, 135, 135)
        }

    # ========== 基础功能测试 ==========

    def test_add_borders_with_array(self, sample_image, default_conf):
        """测试：使用numpy数组作为输入"""
        result = add_gray_borders(sample_image, default_conf)

        assert result.shape == sample_image.shape  # 尺寸不变
        assert result.dtype == np.uint8

        # 检查中间区域是否保持白色（允许小误差）
        center_region = result[:, 400:800]
        assert np.allclose(center_region, 255, atol=5)

        # 检查左右边缘是否变灰
        left_region = result[:, 0:250]
        assert np.mean(left_region) < 200  # 应该比纯白色暗

    def test_add_borders_with_file_path(self, tmp_path, sample_image, default_conf):
        """测试：使用文件路径作为输入"""
        img_path = tmp_path / "test.png"
        cv2.imwrite(str(img_path), sample_image)

        result = add_gray_borders(str(img_path), default_conf)

        assert result.shape == sample_image.shape
        assert result.dtype == np.uint8

    # ========== 边界情况测试 ==========

    def test_content_width_larger_than_image(self, sample_image, default_conf):
        """测试：tire_design_width大于图像宽度"""
        conf = {**default_conf, 'tire_design_width': 1500}
        result = add_gray_borders(sample_image, conf)

        # 应该返回原图（无边框）
        assert np.array_equal(result, sample_image)

    def test_content_width_zero(self, sample_image, default_conf):
        """测试：tire_design_width为0（全灰）"""
        conf = {**default_conf, 'tire_design_width': 0, 'decoration_border_alpha': 0.8}
        result = add_gray_borders(sample_image, conf)

        # 整个图像应该变灰
        assert np.mean(result) < 200

    def test_content_width_equal_to_image(self, sample_image, default_conf):
        """测试：tire_design_width等于图像宽度"""
        conf = {**default_conf, 'tire_design_width': 1200}
        result = add_gray_borders(sample_image, conf)

        # 应该返回原图
        assert np.array_equal(result, sample_image)

    # ========== 参数效果测试 ==========

    def test_alpha_values(self, sample_image, default_conf):
        """测试：不同alpha值的效果"""
        conf_low = {**default_conf, 'decoration_border_alpha': 0.2}
        conf_high = {**default_conf, 'decoration_border_alpha': 0.8}

        result_low = add_gray_borders(sample_image, conf_low)
        result_high = add_gray_borders(sample_image, conf_high)

        # alpha越高，边缘应该越灰
        left_low = np.mean(result_low[:, 0:250])
        left_high = np.mean(result_high[:, 0:250])
        assert left_low > left_high

    def test_custom_gray_color(self, sample_image, default_conf):
        """测试：自定义灰色"""
        conf = {
            **default_conf,
            'decoration_border_alpha': 1.0,  # 完全不透明
            'decoration_gray_color': (100, 100, 100)
        }
        result = add_gray_borders(sample_image, conf)

        # 检查左边缘是否接近指定的灰色
        left_region = result[:, 0:250]
        assert np.allclose(left_region, 100, atol=10)

    def test_default_alpha_value(self, sample_image):
        """测试：使用默认alpha值"""
        conf = {
            'tire_design_width': 700
            # 不提供decoration_border_alpha，应使用默认值0.5
        }
        result = add_gray_borders(sample_image, conf)

        assert result.shape == sample_image.shape
        # 验证边缘确实变灰了
        left_region = result[:, 0:250]
        assert np.mean(left_region) < 200

    def test_default_gray_color(self, sample_image):
        """测试：使用默认灰色"""
        conf = {
            'tire_design_width': 700,
            'decoration_border_alpha': 1.0
            # 不提供decoration_gray_color，应使用默认值(135, 135, 135)
        }
        result = add_gray_borders(sample_image, conf)

        # 检查左边缘是否接近默认灰色
        left_region = result[:, 0:250]
        assert np.allclose(left_region, 135, atol=10)

    # ========== 错误处理测试 ==========

    def test_missing_tire_design_width(self, sample_image):
        """测试：缺少tire_design_width配置"""
        conf = {
            'decoration_border_alpha': 0.5
            # 缺少tire_design_width
        }

        with pytest.raises(ValueError, match="tire_design_width not found in conf"):
            add_gray_borders(sample_image, conf)

    def test_invalid_image_path(self, default_conf):
        """测试：无效的图像路径"""
        with pytest.raises(ValueError, match="无法读取图片"):
            add_gray_borders("/invalid/path.png", default_conf)

    # ========== 真实数据测试 ==========

    def test_real_image_processing(self, default_conf):
        """
        测试：使用真实测试图片

        测试流程：
        1. 从 tests/datasets/task_id_xxx/combine/1.png 复制到 .results/task_id_xxx/combine/1.png
        2. 通过task_id拼接路径
        3. 调用add_gray_borders处理
        4. 验证输出保存到 .results/task_id_xxx/rst/1.png
        """
        task_id = "task_id_f9785e23-8b1c-4a7d-98e7-129876543210"

        # 1. 准备测试数据路径
        source_path = Path("tests/datasets") / task_id / "combine" / "1.png"

        # 检查源文件是否存在
        if not source_path.exists():
            pytest.skip(f"Test image not found: {source_path}")

        # 2. 创建目标目录并复制文件
        target_dir = Path(".results") / task_id / "combine"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / "1.png"

        # 复制文件
        import shutil
        shutil.copy(str(source_path), str(target_path))

        # 3. 处理图片
        result = add_gray_borders(str(target_path), default_conf)

        # 4. 保存结果
        rst_dir = Path(".results") / task_id / "rst"
        rst_dir.mkdir(parents=True, exist_ok=True)
        output_path = rst_dir / "1.png"
        cv2.imwrite(str(output_path), result)

        # 5. 验证
        assert output_path.exists(), "输出文件未生成"

        # 读取输出文件验证
        output_img = cv2.imread(str(output_path))
        assert output_img is not None, "无法读取输出文件"
        assert output_img.shape == result.shape, "输出图像尺寸不匹配"

        # 验证左右边缘确实变灰了
        left_region = output_img[:, :100]
        right_region = output_img[:, -100:]

        # 边缘区域的平均亮度应该低于中间区域
        center_region = output_img[:, output_img.shape[1]//2-50:output_img.shape[1]//2+50]
        assert np.mean(left_region) < np.mean(center_region)
        assert np.mean(right_region) < np.mean(center_region)

        print(f"✓ 真实图片处理成功: {output_path}")
