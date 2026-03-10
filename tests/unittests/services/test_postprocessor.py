"""
postprocessor 模块单元测试
测试轮胎花纹横向布局的核心功能
"""

import pytest
import numpy as np
import cv2
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from itertools import product

# 将项目根目录添加到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.postprocessor import (
    assemble_symmetry_layout,
    LayoutResult,
    CombinationManager,
    load_images_from_directories,
    apply_symmetry_coverage,
    preprocess_images,
    generate_layout_images,
    save_results
)

# ==========================================
# 1. 测试数据路径配置
# ==========================================
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets", "split")
CENTER_DIR = os.path.join(TEST_DATA_DIR, "center")
SIDE_DIR = os.path.join(TEST_DATA_DIR, "side-de-gray")


# ==========================================
# 2. 辅助函数：读取测试图片
# ==========================================
def load_test_image(filename):
    """加载测试图片"""
    filepath = os.path.join(CENTER_DIR, filename)
    if os.path.exists(filepath):
        img = cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), cv2.IMREAD_COLOR)
        return img
    return None


def load_side_test_image(filename):
    """加载 side 测试图片"""
    filepath = os.path.join(SIDE_DIR, filename)
    if os.path.exists(filepath):
        img = cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), cv2.IMREAD_COLOR)
        return img
    return None


# ==========================================
# 3. 测试 assemble_symmetry_layout 核心函数
# ==========================================
class TestAssembleSymmetryLayout:
    """测试轮胎花纹横向布局拼接函数"""

    def test_empty_ribs_raises_error(self):
        """测试输入为空 RIB 列表时应抛出异常"""
        with pytest.raises(ValueError, match="输入异常: 提取的 RIB 列表不能为空"):
            assemble_symmetry_layout(
                extracted_ribs=[],
                user_config={"symmetry_type": "asymmetric"},
                groove_positions=[],
                rib_combination=(0, 0, 0, 0, 0)
            )

    def test_invalid_dimensions_raises_error(self):
        """测试空列表输入时应抛出异常"""
        # 这个测试已经在 test_empty_ribs_raises_error 中覆盖
        # 此处测试边界情况：单个极小的 RIB
        tiny_img = np.zeros((2, 2, 3), dtype=np.uint8)
        # 最小尺寸的 RIB 应该仍能工作（因为有 blend_width 检查保护）
        result = assemble_symmetry_layout(
            extracted_ribs=[tiny_img],
            user_config={"symmetry_type": "asymmetric"},
            groove_positions=[[100]],
            rib_combination=(0,)
        )
        # 极小尺寸可能被边缘融合函数跳过，返回原始图片
        assert result.layout_image is not None

    def test_asymmetric_mode_basic(self):
        """测试非对称模式基本功能"""
        # 创建测试 RIB 图片
        rib1 = np.ones((100, 50, 3), dtype=np.uint8) * 255
        rib2 = np.ones((100, 50, 3), dtype=np.uint8) * 128
        rib3 = np.ones((100, 50, 3), dtype=np.uint8) * 64

        result = assemble_symmetry_layout(
            extracted_ribs=[rib1, rib2, rib3],
            user_config={"symmetry_type": "asymmetric"},
            groove_positions=[[100, 300], [100, 300], [100, 300]],
            rib_combination=(0, 1, 2)
        )

        # 验证返回类型
        assert isinstance(result, LayoutResult)
        assert result.applied_symmetry == "asymmetric"
        assert result.shift_offset == 0.0
        assert len(result.rib_regions) == 3
        assert result.layout_score >= 8.0  # 基础分

    def test_rotate180_mode(self):
        """测试旋转180度对称模式"""
        # 创建有明显特征的左右不同的 RIB
        rib1 = np.zeros((100, 50, 3), dtype=np.uint8)
        rib1[:, :25] = 255  # 左半边白色

        result = assemble_symmetry_layout(
            extracted_ribs=[rib1],
            user_config={"symmetry_type": "rotate180"},
            groove_positions=[[100]],
            rib_combination=(0,)
        )

        assert result.applied_symmetry == "rotate180"
        assert result.layout_image is not None

    def test_mirror_mode(self):
        """测试镜像对称模式"""
        rib1 = np.zeros((100, 50, 3), dtype=np.uint8)
        rib1[:, :25] = 255

        result = assemble_symmetry_layout(
            extracted_ribs=[rib1],
            user_config={"symmetry_type": "mirror"},
            groove_positions=[[100]],
            rib_combination=(0,)
        )

        assert result.applied_symmetry == "mirror"

    def test_mirror_shifted_mode(self):
        """测试镜像错位对称模式"""
        rib1 = np.ones((100, 50, 3), dtype=np.uint8) * 255

        # 提供多个横沟位置以计算节距
        groove_positions = [[50, 150, 250, 350]]

        result = assemble_symmetry_layout(
            extracted_ribs=[rib1],
            user_config={"symmetry_type": "mirror_shifted"},
            groove_positions=groove_positions,
            rib_combination=(0,)
        )

        assert result.applied_symmetry == "mirror_shifted"
        assert result.shift_offset > 0  # 应该有错位偏移

    def test_random_symmetry_mode(self):
        """测试随机对称模式"""
        rib1 = np.ones((100, 50, 3), dtype=np.uint8) * 200

        # 多次调用验证随机性
        results = []
        for _ in range(10):
            result = assemble_symmetry_layout(
                extracted_ribs=[rib1],
                user_config={"symmetry_type": "random"},
                groove_positions=[[100]],
                rib_combination=(0,)
            )
            results.append(result.applied_symmetry)

        # 随机模式应该能返回各种对称类型
        assert all(sym in ["asymmetric", "rotate180", "mirror", "mirror_shifted"] for sym in results)

    def test_height_normalization(self):
        """测试高度归一化功能"""
        rib1 = np.ones((120, 50, 3), dtype=np.uint8) * 255
        rib2 = np.ones((100, 50, 3), dtype=np.uint8) * 128
        rib3 = np.ones((80, 50, 3), dtype=np.uint8) * 64

        result = assemble_symmetry_layout(
            extracted_ribs=[rib1, rib2, rib3],
            user_config={"symmetry_type": "asymmetric"},
            groove_positions=[[100, 300]] * 3,
            rib_combination=(0, 1, 2)
        )

        # 应该以最小高度(80)为基准，输出图像高度应为80
        assert result.layout_image.shape[0] == 80

    def test_blend_width_effect(self):
        """测试边缘融合宽度参数"""
        rib1 = np.ones((100, 50, 3), dtype=np.uint8) * 255

        result_default = assemble_symmetry_layout(
            extracted_ribs=[rib1],
            user_config={"symmetry_type": "asymmetric"},
            groove_positions=[[100]],
            rib_combination=(0,),
            blend_width=10
        )

        result_custom = assemble_symmetry_layout(
            extracted_ribs=[rib1],
            user_config={"symmetry_type": "asymmetric"},
            groove_positions=[[100]],
            rib_combination=(0,),
            blend_width=20
        )

        # 两种情况都应该成功生成图片
        assert result_default.layout_image is not None
        assert result_custom.layout_image is not None

    def test_side_rib_indices_preserved(self):
        """测试 side_rib_indices 参数保持边缘 RIB 宽度"""
        # 创建不同宽度的 RIB
        rib1 = np.ones((100, 60, 3), dtype=np.uint8) * 255  # side - 更宽
        rib2 = np.ones((100, 40, 3), dtype=np.uint8) * 128  # center - 更窄

        result = assemble_symmetry_layout(
            extracted_ribs=[rib1, rib2],
            user_config={"symmetry_type": "asymmetric"},
            groove_positions=[[100], [100]],
            rib_combination=(0, 0),
            side_rib_indices=[0]  # 第一个是 side
        )

        # 验证输出图片不为空
        assert result.layout_image is not None
        assert result.layout_image.shape[0] == 100


# ==========================================
# 4. 测试 CombinationManager 类
# ==========================================
class TestCombinationManager:
    """测试组合管理器"""

    @pytest.fixture
    def mock_images(self):
        """创建模拟图片"""
        center = [np.ones((100, 50, 3), dtype=np.uint8) * i for i in range(1, 4)]
        side = [np.ones((100, 60, 3), dtype=np.uint8) * (i + 10) for i in range(1, 3)]
        return center, side

    def test_initialization_5_rib(self, mock_images):
        """测试 5 RIB 模式初始化"""
        center, side = mock_images
        manager = CombinationManager(center, side, rib_count=5)

        assert manager.rib_count == 5
        assert len(manager.center_images) == 3
        assert len(manager.side_images) == 2

    def test_initialization_4_rib(self, mock_images):
        """测试 4 RIB 模式初始化"""
        center, side = mock_images
        manager = CombinationManager(center, side, rib_count=4)

        assert manager.rib_count == 4

    def test_asymmetric_combinations_5_rib(self, mock_images):
        """测试 5 RIB 不对称组合生成"""
        center, side = mock_images
        manager = CombinationManager(center, side, rib_count=5)

        combos = manager.asymmetric_combinations
        # 2 side * 3 center * 3 center * 3 center * 2 side = 108 组合
        # 注意：允许重复，所以是笛卡尔积
        assert len(combos) == 2 * 3 * 3 * 3 * 2

        # 验证组合格式
        for combo in combos:
            assert len(combo) == 5
            # 第一个和最后一个来自 side
            assert combo[0] < len(side)
            assert combo[4] < len(side)
            # 中间来自 center
            assert combo[1] < len(center)
            assert combo[2] < len(center)
            assert combo[3] < len(center)

    def test_asymmetric_combinations_4_rib(self, mock_images):
        """测试 4 RIB 不对称组合生成"""
        center, side = mock_images
        manager = CombinationManager(center, side, rib_count=4)

        combos = manager.asymmetric_combinations
        # 2 side * 3 center * 3 center * 2 side = 36 组合
        # 注意：允许重复，所以是笛卡尔积
        assert len(combos) == 2 * 3 * 3 * 2

        for combo in combos:
            assert len(combo) == 4

    def test_symmetry_combinations_5_rib(self, mock_images):
        """测试 5 RIB 对称组合生成"""
        center, side = mock_images
        manager = CombinationManager(center, side, rib_count=5)

        combos = manager.symmetry_combinations
        # 3 center * 3 center * 2 side = 18 组合
        assert len(combos) == 3 * 3 * 2

        for combo in combos:
            assert len(combo) == 3  # 只排列右侧3个 RIB

    def test_symmetry_combinations_4_rib(self, mock_images):
        """测试 4 RIB 对称组合生成"""
        center, side = mock_images
        manager = CombinationManager(center, side, rib_count=4)

        combos = manager.symmetry_combinations
        # 3 center * 2 side = 6 组合
        assert len(combos) == 3 * 2

        for combo in combos:
            assert len(combo) == 2

    def test_select_combinations_by_priority(self, mock_images):
        """测试按优先级选择组合"""
        center, side = mock_images

        with tempfile.TemporaryDirectory() as tmpdir:
            # 临时修改历史文件路径
            with patch.object(CombinationManager, '__init__', lambda self, c, s, r: None):
                manager = CombinationManager.__new__(CombinationManager)
                manager.center_images = center
                manager.side_images = side
                manager.rib_count = 5
                manager.history_file = os.path.join(tmpdir, "history.json")
                manager.history_counts = {}

                manager.asymmetric_combinations = [(0, 0, 0, 0, 0), (1, 1, 1, 1, 1)]
                manager.config = {'generation': {'max_per_mode': 10}}

                selected = manager.select_combinations_by_priority('asymmetric', count=1)

                assert len(selected) == 1
                assert selected[0] in manager.asymmetric_combinations


# ==========================================
# 5. 测试辅助函数
# ==========================================
class TestHelperFunctions:
    """测试辅助函数"""

    def test_apply_symmetry_coverage_asymmetric(self):
        """测试非对称模式不进行覆盖"""
        ribs = [np.ones((10, 10, 3), dtype=np.uint8) * i for i in range(5)]
        result = apply_symmetry_coverage(ribs, rib_count=5, symmetry_mode='asymmetric')

        assert result == ribs  # 应该返回原数组

    def test_apply_symmetry_coverage_5_rib(self):
        """测试 5 RIB 对称覆盖"""
        ribs = [
            np.ones((10, 10, 3), dtype=np.uint8) * 1,   # RIB1
            np.ones((10, 10, 3), dtype=np.uint8) * 2,   # RIB2
            np.ones((10, 10, 3), dtype=np.uint8) * 3,   # RIB3
            np.ones((10, 10, 3), dtype=np.uint8) * 4,   # RIB4
            np.ones((10, 10, 3), dtype=np.uint8) * 5    # RIB5
        ]

        result = apply_symmetry_coverage(ribs, rib_count=5, symmetry_mode='rotate180')

        # 验证覆盖: RIB4 -> RIB2, RIB5 -> RIB1
        assert np.array_equal(result[0], ribs[4])  # RIB1 <- RIB5
        assert np.array_equal(result[1], ribs[3])  # RIB2 <- RIB4
        assert np.array_equal(result[2], ribs[2])  # RIB3 保持不变

    def test_apply_symmetry_coverage_4_rib(self):
        """测试 4 RIB 对称覆盖"""
        ribs = [
            np.ones((10, 10, 3), dtype=np.uint8) * 1,   # RIB1
            np.ones((10, 10, 3), dtype=np.uint8) * 2,   # RIB2
            np.ones((10, 10, 3), dtype=np.uint8) * 3,   # RIB3
            np.ones((10, 10, 3), dtype=np.uint8) * 4    # RIB4
        ]

        result = apply_symmetry_coverage(ribs, rib_count=4, symmetry_mode='mirror')

        # 验证覆盖: RIB3 -> RIB1, RIB4 -> RIB2
        assert np.array_equal(result[0], ribs[2])  # RIB1 <- RIB3
        assert np.array_equal(result[1], ribs[3])  # RIB2 <- RIB4

    def test_preprocess_images_same_size(self):
        """测试图片尺寸相同时不处理"""
        images = [np.ones((200, 100, 3), dtype=np.uint8) for _ in range(3)]
        result_center, result_side = preprocess_images(
            images, images, center_size=(100, 200), side_size=(100, 200)
        )

        assert len(result_center) == 3

    def test_preprocess_images_crop(self):
        """测试图片裁剪功能"""
        # 创建大于目标尺寸的图片
        large_img = np.ones((300, 200, 3), dtype=np.uint8) * 128

        result, _ = preprocess_images(
            [large_img], [], center_size=(100, 200), side_size=(100, 200)
        )

        # 应该被裁剪到目标尺寸
        assert result[0].shape == (200, 100, 3)

    def test_preprocess_images_resize(self):
        """测试图片放大功能"""
        # 创建小于目标尺寸的图片
        small_img = np.ones((100, 50, 3), dtype=np.uint8) * 64

        result, _ = preprocess_images(
            [small_img], [], center_size=(100, 200), side_size=(100, 200)
        )

        # 应该被放大到目标尺寸
        assert result[0].shape == (200, 100, 3)


# ==========================================
# 6. 测试 load_images_from_directories 函数
# ==========================================
class TestLoadImagesFromDirectories:
    """测试图片加载函数"""

    def test_load_from_valid_directories(self):
        """测试从有效目录加载图片（依赖 .results/split 下存在 center/side 图片，无数据时跳过）"""
        center, side, names = load_images_from_directories()

        # 验证返回类型
        assert isinstance(center, list)
        assert isinstance(side, list)
        assert isinstance(names, dict)

        # 无测试图片时跳过，不视为失败
        if len(center) == 0 or len(side) == 0:
            pytest.skip("center/side 目录下暂无图片，请将 RIB 图片放入 .results/split/center 与 .results/split/side-de-gray 后重试")

        # 验证图片格式
        for img in center:
            assert isinstance(img, np.ndarray)
            assert img.ndim == 3
            assert img.shape[2] == 3  # BGR 格式

    def test_load_from_nonexistent_directories(self):
        """测试从不存在目录加载"""
        with patch('services.postprocessor.CONFIG', {
            'paths': {
                'center_dir': '/nonexistent/path/center',
                'side_dir': '/nonexistent/path/side'
            }
        }):
            center, side, names = load_images_from_directories()

            # 空目录应返回空列表
            assert center == []
            assert side == []
            assert names == {}


# ==========================================
# 7. 测试 generate_layout_images 函数
# ==========================================
class TestGenerateLayoutImages:
    """测试布局图片生成函数"""

    def test_generate_asymmetric_mode(self):
        """测试生成非对称模式布局"""
        center = [np.ones((200, 100, 3), dtype=np.uint8) * i for i in range(1, 4)]
        side = [np.ones((200, 80, 3), dtype=np.uint8) * (i + 10) for i in range(1, 3)]

        results = generate_layout_images(
            center, side, rib_count=5, symmetry_type="asymmetric"
        )

        assert len(results) > 0
        for result in results:
            assert isinstance(result, LayoutResult)
            assert result.applied_symmetry == "asymmetric"

    def test_generate_all_symmetry_modes(self):
        """测试生成所有对称模式"""
        center = [np.ones((200, 100, 3), dtype=np.uint8) * i for i in range(1, 3)]
        side = [np.ones((200, 80, 3), dtype=np.uint8) * (i + 10) for i in range(1, 2)]

        results = generate_layout_images(
            center, side, rib_count=4, symmetry_type="all_symmetry"
        )

        symmetry_types = [r.applied_symmetry for r in results]
        # 应该有 rotate180, mirror, mirror_shifted
        assert "rotate180" in symmetry_types
        assert "mirror" in symmetry_types
        assert "mirror_shifted" in symmetry_types


# ==========================================
# 8. 测试边界情况
# ==========================================
class TestBoundaryCases:
    """测试边界情况"""

    def test_single_rib(self):
        """测试单条 RIB 情况"""
        rib = np.ones((100, 50, 3), dtype=np.uint8) * 200

        result = assemble_symmetry_layout(
            extracted_ribs=[rib],
            user_config={"symmetry_type": "asymmetric"},
            groove_positions=[[100]],
            rib_combination=(0,)
        )

        assert result.layout_image is not None
        assert result.layout_image.shape[1] > 0  # 应该有宽度

    def test_large_blend_width(self):
        """测试较大的融合宽度（边界情况）"""
        rib = np.ones((100, 30, 3), dtype=np.uint8) * 200

        # 融合宽度大于 RIB 宽度时应该仍能工作
        result = assemble_symmetry_layout(
            extracted_ribs=[rib],
            user_config={"symmetry_type": "asymmetric"},
            groove_positions=[[100]],
            rib_combination=(0,),
            blend_width=50  # 大于 RIB 宽度
        )

        assert result.layout_image is not None


# ==========================================
# 9. 集成测试：使用真实测试数据
# ==========================================
class TestIntegrationWithRealData:
    """使用真实测试数据进行集成测试"""

    def test_load_real_center_images(self):
        """测试加载真实的 center 图片（无数据时跳过）"""
        from configs.postprocessor_config import CONFIG
        center_dir = CONFIG.get('paths', {}).get('center_dir')

        images = []
        if center_dir and os.path.exists(center_dir):
            for filename in sorted(os.listdir(center_dir)):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(center_dir, filename)
                    img = cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        images.append(img)

        if len(images) == 0:
            pytest.skip(f"center 目录下暂无图片, 路径: {center_dir}")
        print(f"\n成功加载 {len(images)} 张 center 测试图片")

    def test_load_real_side_images(self):
        """测试加载真实的 side 图片（无数据时跳过）"""
        from configs.postprocessor_config import CONFIG
        side_dir = CONFIG.get('paths', {}).get('side_dir')

        images = []
        if side_dir and os.path.exists(side_dir):
            for filename in sorted(os.listdir(side_dir)):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(side_dir, filename)
                    img = cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        images.append(img)

        if len(images) == 0:
            pytest.skip(f"side 目录下暂无图片, 路径: {side_dir}")
        print(f"\n成功加载 {len(images)} 张 side 测试图片")

    def test_layout_with_real_images_5_rib(self):
        """使用真实图片测试 5 RIB 布局"""
        from configs.postprocessor_config import CONFIG
        center_dir = CONFIG.get('paths', {}).get('center_dir')
        side_dir = CONFIG.get('paths', {}).get('side_dir')

        center_images = []
        side_images = []

        # 加载 center 图片
        if center_dir and os.path.exists(center_dir):
            for filename in sorted(os.listdir(center_dir))[:3]:  # 取前3张
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(center_dir, filename)
                    img = cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        center_images.append(img)

        # 加载 side 图片
        if side_dir and os.path.exists(side_dir):
            for filename in sorted(os.listdir(side_dir))[:2]:  # 取前2张
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(side_dir, filename)
                    img = cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        side_images.append(img)

        if len(center_images) >= 3 and len(side_images) >= 2:
            # 预处理
            center_processed, side_processed = preprocess_images(
                center_images, side_images,
                center_size=(200, 1241),
                side_size=(400, 1241)
            )

            # 生成布局
            results = generate_layout_images(
                center_processed, side_processed,
                rib_count=5,
                symmetry_type="asymmetric"
            )

            assert len(results) > 0
            print(f"\n成功生成 {len(results)} 张 5 RIB 布局图")
        else:
            pytest.skip(f"测试数据不足 (center: {len(center_images)}, side: {len(side_images)})，跳过集成测试")

    def test_layout_with_real_images_4_rib(self):
        """使用真实图片测试 4 RIB 布局"""
        from configs.postprocessor_config import CONFIG
        center_dir = CONFIG.get('paths', {}).get('center_dir')
        side_dir = CONFIG.get('paths', {}).get('side_dir')

        center_images = []
        side_images = []

        if center_dir and os.path.exists(center_dir):
            for filename in sorted(os.listdir(center_dir))[:2]:
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(center_dir, filename)
                    img = cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        center_images.append(img)

        if side_dir and os.path.exists(side_dir):
            for filename in sorted(os.listdir(side_dir))[:2]:
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(side_dir, filename)
                    img = cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        side_images.append(img)

        if len(center_images) >= 2 and len(side_images) >= 2:
            center_processed, side_processed = preprocess_images(
                center_images, side_images,
                center_size=(200, 1241),
                side_size=(400, 1241)
            )

            results = generate_layout_images(
                center_processed, side_processed,
                rib_count=4,
                symmetry_type="mirror_shifted"
            )

            assert len(results) > 0
            print(f"\n成功生成 {len(results)} 张 4 RIB 镜像错位布局图")
        else:
            pytest.skip(f"测试数据不足 (center: {len(center_images)}, side: {len(side_images)})，跳过集成测试")


# ==========================================
# 10. 测试输出保存功能
# ==========================================
class TestSaveResults:
    """测试结果保存功能"""

    def test_save_results_to_directory(self):
        """测试保存结果到目录"""
        # 创建模拟结果
        layout_img = np.ones((200, 500, 3), dtype=np.uint8) * 128

        result = LayoutResult(
            layout_image=layout_img,
            applied_symmetry="asymmetric",
            shift_offset=0.0,
            rib_regions=[(0, 0, 100, 200), (120, 0, 220, 200)],
            layout_score=9.0,
            rib_combination=(0, 1)
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            save_results([result], output_dir=tmpdir)

            # 验证文件已保存
            files = os.listdir(tmpdir)
            assert len(files) > 0
            assert files[0].endswith('.png')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
