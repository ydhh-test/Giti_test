# -*- coding: utf-8 -*-

"""
后处理模块

后处理主逻辑包括：
1，小图筛选阶段
2，拼图阶段
3，大图打分阶段
4，输出整理阶段
"""


from algorithms.stitching.vertical_stitch import VerticalStitch


def postprocessor(task_id: str, conf: dict, user_conf: dict) -> tuple[int, dict]:
    """
    后处理入口函数

    Args:
        task_id: 任务ID
        conf: 配置字典（支持旧格式和新格式）
        user_conf: 用户配置字典

    Returns:
        tuple[int, dict]: (score, details)
    """
    # 0. Conf处理 - 向后兼容处理
    try:
        from configs import CompleteConfig
        if isinstance(conf, CompleteConfig):
            merged_conf = {**conf.to_legacy_dict(), **user_conf}
        else:
            merged_conf = _merge_conf(conf, user_conf)
    except ImportError:
        merged_conf = _merge_conf(conf, user_conf)

    # 1. 小图筛选
    small_image_filter_conf = merged_conf.get("small_image_filter_conf", {})
    flag, details = _small_image_filter(task_id, small_image_filter_conf)
    if not flag:
        return 0, {**details, "failed_stage": "small_image_filter"}

    # 2. 纵图拼接
    vertical_stitch_conf = merged_conf.get("vertical_stitch_conf", {})
    flag, details = _vertical_stitch(task_id, vertical_stitch_conf)
    if not flag:
        return 0, {**details, "failed_stage": "vertical_stitch"}

    # 3. 横图拼接
    horizontal_stitch_conf = merged_conf.get("horizontal_stitch_conf", {})
    flag, details = _horizontal_stitch(task_id, horizontal_stitch_conf)
    if not flag:
        return 0, {**details, "failed_stage": "horizontal_stitch"}

    # 4. 装饰边框
    decoration_conf = merged_conf.get("decoration_conf", {})
    flag, details = _add_decoration_borders(task_id, decoration_conf, merged_conf)
    if not flag:
        return 0, {**details, "failed_stage": "decoration_borders"}

    # 5. 统计总分
    calculate_total_score_conf = merged_conf.get("calculate_total_score_conf", {})
    flag, details = _calculate_total_score(task_id, calculate_total_score_conf)
    if not flag:
        return 0, {**details, "failed_stage": "calculate_total_score"}

    # TODO: 6. 整理输出 (暂不实现)

    # 当前不实装，从 conf 中获取总分
    score = 0
    return score, details


def _merge_conf(conf: dict, user_conf: dict) -> dict:
    """合并配置"""
    merged = conf.copy()
    merged.update(user_conf)
    return merged


def _small_image_filter(task_id: str, conf: dict) -> tuple[bool, dict]:
    """小图筛选"""
    # TODO: 实现小图筛选逻辑
    return True, {}


def _vertical_stitch(task_id: str, conf: dict) -> tuple[bool, dict]:
    """纵图拼接"""
    # 传递完整的配置给VerticalStitch，以便访问所有配置参数
    stitcher = VerticalStitch(task_id, conf)
    return stitcher.process()


def _horizontal_stitch(task_id: str, conf: dict) -> tuple[bool, dict]:
    """横图拼接"""
    # TODO: 实现横图拼接逻辑
    return True, {}


def _calculate_total_score(task_id: str, conf: dict) -> tuple[bool, dict]:
    """统计总分"""
    # TODO: 实现统计总分逻辑
    return True, {}


def _add_decoration_borders(task_id: str, conf: dict, merged_conf: dict) -> tuple[bool, dict]:
    """
    添加装饰边框

    Args:
        task_id: 任务ID
        conf: 装饰边框配置
        merged_conf: 完整配置（包含用户配置）

    Returns:
        tuple[bool, dict]: (是否成功, 详情字典)
    """
    from utils.cv_utils import add_gray_borders
    from pathlib import Path
    import cv2

    # 1. 检查必需配置
    if 'tire_design_width' not in merged_conf:
        return False, {"error": "tire_design_width not configured"}

    # 2. 确定输入输出路径
    base_path = Path(".results") / task_id
    combine_dir = base_path / "combine"
    rst_dir = base_path / "rst"
    rst_dir.mkdir(parents=True, exist_ok=True)

    # 3. 检查输入目录
    if not combine_dir.exists():
        return False, {"error": f"combine directory not found: {combine_dir}"}

    # 4. 处理所有拼接完成的大图
    processed_files = []
    decoration_style = merged_conf.get('decoration_style', 'simple')

    for img_path in combine_dir.glob("*.png"):
        try:
            # 根据装饰风格选择处理方式
            if decoration_style == 'simple':
                # 调用add_gray_borders，传入conf
                result = add_gray_borders(str(img_path), merged_conf)
            else:
                # 未来可以扩展其他风格
                return False, {"error": f"Unsupported decoration_style: {decoration_style}"}

            # 保存结果
            output_path = rst_dir / img_path.name
            cv2.imwrite(str(output_path), result)
            processed_files.append(str(output_path))

        except Exception as e:
            return False, {"error": f"Failed to process {img_path}: {str(e)}"}

    return True, {
        "processed_files": processed_files,
        "decoration_style": decoration_style,
        "tdw": merged_conf.get('tire_design_width'),
        "alpha": merged_conf.get('decoration_border_alpha', 0.5)
    }


# ==========================================
# 从 dev_lxl 迁移的布局生成模块
# ==========================================
import cv2
import numpy as np
import random
import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, NamedTuple
from itertools import product
from collections import defaultdict

# 将项目根目录添加到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置加载
try:
    from configs.postprocessor_config import (
        CONFIG, RIB_CONFIG, GENERATION_CONFIG, INTERNAL_CONFIG, SYMMETRY_MAPPING
    )
except ImportError:
    CONFIG = {}
    RIB_CONFIG = {}
    GENERATION_CONFIG = {}
    INTERNAL_CONFIG = {}
    SYMMETRY_MAPPING = {}


class LayoutResult(NamedTuple):
    """
    【功能】
    定义轮胎花纹横向布局函数的标准返回结构。
    使用 NamedTuple 既保证了数据解包的便利性，又保证了返回结果的不可变性（安全性）。

    【字段说明】
    - layout_image: np.ndarray。最终拼接并经过对称变换后的横向布局图 (BGR 格式)。
    - applied_symmetry: str。实际应用到图像上的对称策略（如 "mirror_shifted"），若输入为 "random"，此字段记录随机选中的实际策略。
    - shift_offset: float。在 "mirror_shifted"（镜像错位）模式下，左侧半幅图像在 Y 轴（纵向）平移的像素量。非错位模式下该值为 0.0。
    - rib_regions: List[Tuple[int, int, int, int]]。记录每个提取出的 RIB 在初始拼接画布中的坐标范围，格式为 [x_start, y_start, x_end, y_end]。
    - layout_score: float。布局质量的参考得分，当前为基础模拟分。
    - rib_combination: Tuple。使用的 RIB 组合索引。
    """
    layout_image: np.ndarray
    applied_symmetry: str
    shift_offset: float
    rib_regions: List[Tuple[int, int, int, int]]
    layout_score: float
    rib_combination: Tuple


def assemble_symmetry_layout(
    extracted_ribs: List[np.ndarray],
    user_config: Dict[str, Any],
    groove_positions: List[List[int]],
    rib_combination: Tuple = None,
    blend_width: int = None,
    side_rib_indices: List[int] = None
) -> LayoutResult:
    """
    【函数功能】
    根据给定的 RIB 图像数组、横沟坐标以及用户指定的对称策略，生成无缝拼接的轮胎花纹横向布局图。

    【实现逻辑】
    1. 校验输入的所有 RIB 图像的高度是否一致。
    2. 将传入的 RIB 数组按照从左到右的顺序，间隔 main_groove_width（主沟宽度）进行初始拼合（非对称画布），同时在 RIB 的左右边缘应用 Alpha 线性渐变以实现向主沟背景的平滑过渡。
    3. 计算所有横沟在 Y 轴上的平均间距（节距 Pitch），以确定错位模式下的平移量（平均节距的 1/2）。
    4. 沿着全局画布的中轴线进行切分，提取右半幅图像，根据 symmetry_type 执行几何变换（旋转 180°、镜像、镜像且沿 Y 轴 wrap-around 卷动补齐），然后用变换后的结果覆写左半幅画布。
    5. 组装并返回 LayoutResult 结果对象。
    """

    if side_rib_indices is None:
        side_rib_indices = []

    # 使用配置中的默认值
    if blend_width is None:
        blend_width = CONFIG.get('internal', {}).get('blend_width', 10)
    main_groove_width = CONFIG.get('internal', {}).get('main_groove_width', 20)

    # 1. 防御性检查与高度对齐（按本组最小高度裁剪，不做缩放/补边）
    if not extracted_ribs:
        raise ValueError("输入异常: 提取的 RIB 列表不能为空。")

    # 以当前组合中"高度最小的那条 RIB"为基准高度
    target_h = min(rib.shape[0] for rib in extracted_ribs)

    normalized_ribs = []
    for rib in extracted_ribs:
        h, w, c = rib.shape

        if h == target_h:
            normalized_ribs.append(rib)
        else:
            y_start = (h - target_h) // 2
            y_end = y_start + target_h
            cropped = rib[y_start:y_end, :, :]
            normalized_ribs.append(cropped)

    extracted_ribs = normalized_ribs
    img_h = target_h

    # 统一每条 RIB 的宽度
    non_side_ribs = [rib for i, rib in enumerate(extracted_ribs) if i not in side_rib_indices]
    if non_side_ribs:
        target_w = min(rib.shape[1] for rib in non_side_ribs)
    else:
        target_w = min(rib.shape[1] for rib in extracted_ribs)

    if target_w <= 0 or target_h <= 0:
        raise ValueError(
            f"输入异常: 归一化后 RIB 尺寸无效 (target_h={target_h}, target_w={target_w})，请检查输入图片尺寸。"
        )

    normalized_width_ribs = []
    for i, rib in enumerate(extracted_ribs):
        h, w, c = rib.shape
        if i in side_rib_indices:
            normalized_width_ribs.append(rib)
        elif w == target_w:
            normalized_width_ribs.append(rib)
        else:
            x_start = (w - target_w) // 2
            x_end = x_start + target_w
            cropped = rib[:, x_start:x_end, :]
            normalized_width_ribs.append(cropped)

    extracted_ribs = normalized_width_ribs

    num_ribs = len(extracted_ribs)
    main_groove_count = num_ribs - 1

    # 2. 基础非对称拼接与 Alpha 渐变边缘融合
    total_rib_width = sum(rib.shape[1] for rib in extracted_ribs)
    total_layout_width = total_rib_width + (main_groove_count * main_groove_width)

    layout_img = np.zeros((img_h, total_layout_width, 3), dtype=np.uint8)
    current_x = 0
    rib_regions = []

    def apply_edge_blend(img: np.ndarray, bw: int, is_first: bool, is_last: bool) -> np.ndarray:
        h, w, c = img.shape
        if w <= 2 * bw:
            return img

        mask = np.ones((1, w, 1), dtype=np.float32)

        if not is_first:
            mask[:, :bw, :] = np.linspace(0.0, 1.0, bw).reshape(1, bw, 1)
        if not is_last:
            mask[:, -bw:, :] = np.linspace(1.0, 0.0, bw).reshape(1, bw, 1)

        return (img.astype(np.float32) * mask).astype(np.uint8)

    for i, rib in enumerate(extracted_ribs):
        is_first_rib = (i == 0)
        is_last_rib = (i == num_ribs - 1)

        blended_rib = apply_edge_blend(rib, blend_width, is_first_rib, is_last_rib)

        rib_w = blended_rib.shape[1]
        x_end = current_x + rib_w

        layout_img[:, current_x:x_end] = blended_rib
        rib_regions.append((current_x, 0, x_end, img_h))

        current_x = x_end + main_groove_width

    # 3. 动态计算平均节距 (Pitch) 决定平移量
    pitch_diffs = []
    for rib_grooves in groove_positions:
        if len(rib_grooves) > 1:
            pitch_diffs.extend(np.diff(rib_grooves))

    avg_pitch = np.mean(pitch_diffs) if pitch_diffs else 0.0
    shift_offset = avg_pitch / 2.0

    # 4. 全局几何变换与对称路由
    valid_modes = ["asymmetric", "rotate180", "mirror", "mirror_shifted"]
    symmetry_mode = user_config.get("symmetry_type", "asymmetric")

    if symmetry_mode == "random":
        symmetry_mode = random.choice(valid_modes)

    applied_symmetry = symmetry_mode

    if symmetry_mode != "asymmetric":
        if total_layout_width < 2:
            raise ValueError(
                f"输入异常: 画布总宽度过小 (total_layout_width={total_layout_width})，无法进行对称覆写，请检查 RIB 宽度与数量。"
            )
        # 修正: 如果 rib 数量是偶数 (如 4-RIB), 中间有一条完整的主沟(main_groove)
        # 传统的 // 2 会把最中间的主沟切分并镜像导致沟变宽或消失。
        # 我们需要保留中间的那条主沟不被镜像覆盖
        if num_ribs % 2 == 0:
            # 找到中间那条沟的起始 x 坐标
            # 对于 4-RIB, 中间的沟是第二条沟 (index 1)
            mid_groove_idx = num_ribs // 2 - 1
            left_rib_end = rib_regions[mid_groove_idx][2]
            right_rib_start = rib_regions[mid_groove_idx + 1][0]
            
            left_half_w = left_rib_end
            right_half_start = right_rib_start
            right_half_w = total_layout_width - right_half_start
        else:
            mid_x = total_layout_width // 2
            right_half_start = mid_x
            left_half_w = mid_x
            right_half_w = total_layout_width - mid_x

        right_half = layout_img[:, right_half_start: total_layout_width].copy()

        if symmetry_mode == "rotate180":
            transformed_half = cv2.rotate(right_half, cv2.ROTATE_180)
        elif symmetry_mode == "mirror":
            transformed_half = cv2.flip(right_half, 1)
        elif symmetry_mode == "mirror_shifted":
            mirrored = cv2.flip(right_half, 1)
            transformed_half = np.roll(mirrored, shift=int(shift_offset), axis=0)

        copy_w = min(left_half_w, right_half_w)
        if copy_w > 0:
            left_start = left_half_w - copy_w
            layout_img[:, left_start:left_half_w] = transformed_half[:, :copy_w]

    # ==========================================
    # 5. 裁剪左右两侧全黑或近黑画布 (约束规则)
    # 强制去除左侧(RIB1外侧)和右侧(最后一个RIB外侧)的冗余区域
    # 使用灰度阈值，能够剪裁掉带有图片自带微弱噪声黑边的情况
    # ==========================================
    gray_layout = cv2.cvtColor(layout_img, cv2.COLOR_BGR2GRAY)
    black_threshold = 15  # 亮度阈值配置：低于此亮度视作待裁切纯黑
    non_black_cols = np.where(np.any(gray_layout > black_threshold, axis=0))[0]
    
    if len(non_black_cols) > 0:
        first_col = int(non_black_cols[0])
        last_col = int(non_black_cols[-1])
        if first_col > 0 or last_col < layout_img.shape[1] - 1:
            layout_img = layout_img[:, first_col:last_col + 1].copy()
            
            # 修正 rib_regions 的坐标
            adjusted_regions = []
            for (rx_start, ry_start, rx_end, ry_end) in rib_regions:
                new_start = max(0, rx_start - first_col)
                new_end = max(0, rx_end - first_col)
                adjusted_regions.append((new_start, ry_start, new_end, ry_end))
            rib_regions = adjusted_regions

    # 6. 质量评估与组装返回
    base_score = 8.0
    extra_score = 1.0 if applied_symmetry == user_config.get("symmetry_type") else 0.0
    layout_score = base_score + extra_score

    return LayoutResult(
        layout_image=layout_img,
        applied_symmetry=applied_symmetry,
        shift_offset=shift_offset if symmetry_mode == "mirror_shifted" else 0.0,
        rib_regions=rib_regions,
        layout_score=layout_score,
        rib_combination=rib_combination
    )


# 全排列组合管理
class CombinationManager:
    """全排列组合管理器"""

    def __init__(self, center_images: List, side_images: List, rib_count: int):
        self.center_images = center_images
        self.side_images = side_images
        self.rib_count = rib_count
        self.config = CONFIG

        history_path = self.config.get('generation', {}).get('history_file', '.results/data/history_counts.json')
        if not os.path.isabs(history_path):
            history_path = os.path.join(os.path.dirname(__file__), '..', history_path)
        self.history_file = history_path

        self.history_counts = self._load_history()

        self.asymmetric_combinations = self._generate_asymmetric_combinations()
        self.symmetry_combinations = self._generate_symmetry_combinations()

    def _load_history(self) -> Dict:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return defaultdict(int)
        return defaultdict(int)

    def _save_history(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(dict(self.history_counts), f, ensure_ascii=False, indent=2)

    def _generate_asymmetric_combinations(self) -> List[Tuple]:
        side_indices = list(range(len(self.side_images)))
        center_indices = list(range(len(self.center_images)))

        if self.rib_count == 5:
            side_combinations = list(product(side_indices, repeat=2))
            center_combinations = list(product(center_indices, repeat=3))

            combinations = []
            for side_combo in side_combinations:
                for center_combo in center_combinations:
                    combinations.append((side_combo[0], center_combo[0], center_combo[1], center_combo[2], side_combo[1]))
        else:  # 4 RIB 模式
            side_combinations = list(product(side_indices, repeat=2))
            center_combinations = list(product(center_indices, repeat=2))

            combinations = []
            for side_combo in side_combinations:
                for center_combo in center_combinations:
                    combinations.append((side_combo[0], center_combo[0], center_combo[1], side_combo[1]))

        return combinations

    def _generate_symmetry_combinations(self) -> List[Tuple]:
        center_indices = list(range(len(self.center_images)))
        side_indices = list(range(len(self.side_images)))

        if self.rib_count == 5:
            combinations = []
            for rib3_idx in center_indices:
                for rib4_idx in center_indices:
                    for rib5_idx in side_indices:
                        combinations.append((rib3_idx, rib4_idx, rib5_idx))
        else:  # 4 RIB 模式
            combinations = []
            for rib3_idx in center_indices:
                for rib4_idx in side_indices:
                    combinations.append((rib3_idx, rib4_idx))

        return combinations

    def _get_combo_key(self, combo: Tuple, mode: str) -> str:
        return f"{mode}_{combo}"

    def select_combinations_by_priority(self, mode: str, count: int = None) -> List[Tuple]:
        if count is None:
            count = self.config.get('generation', {}).get('max_per_mode', 10)

        if mode == 'asymmetric':
            combinations = self.asymmetric_combinations
        else:
            combinations = self.symmetry_combinations

        if not combinations:
            return []

        combo_with_counts = []
        for combo in combinations:
            key = self._get_combo_key(combo, mode)
            cnt = self.history_counts.get(key, 0)
            combo_with_counts.append((combo, cnt))

        combo_with_counts.sort(key=lambda x: x[1])

        selected = [combo for combo, _ in combo_with_counts[:count]]

        for combo in selected:
            key = self._get_combo_key(combo, mode)
            self.history_counts[key] = self.history_counts.get(key, 0) + 1

        self._save_history()

        return selected


def load_images_from_directories() -> Tuple[List, List, Dict]:
    """从 center 和 side 目录读取所有图片，按来源重命名"""
    center_dir = CONFIG.get('paths', {}).get('center_dir')
    side_dir = CONFIG.get('paths', {}).get('side_dir')

    center_images = []
    side_images = []
    image_names = {}

    if os.path.exists(center_dir):
        for idx, filename in enumerate(sorted(os.listdir(center_dir))):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                img_path = os.path.join(center_dir, filename)
                img = cv2.imread(img_path)
                if img is not None:
                    center_images.append(img)
                    image_names[f'center_{idx}'] = filename

    if os.path.exists(side_dir):
        for idx, filename in enumerate(sorted(os.listdir(side_dir))):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                img_path = os.path.join(side_dir, filename)
                img = cv2.imread(img_path)
                if img is not None:
                    side_images.append(img)
                    image_names[f'side_{idx}'] = filename

    return center_images, side_images, image_names


def apply_symmetry_coverage(
    ribs: List[np.ndarray],
    rib_count: int,
    symmetry_mode: str
) -> List[np.ndarray]:
    """应用对称覆盖策略"""
    if symmetry_mode == 'asymmetric':
        return ribs

    result = list(ribs)

    if rib_count == 5:
        result[1] = ribs[3].copy()
        result[0] = ribs[4].copy()
    else:  # 4 RIB 模式
        result[0] = ribs[3].copy()
        result[1] = ribs[2].copy()

    return result


def preprocess_images(
    center_images: List[np.ndarray],
    side_images: List[np.ndarray],
    center_size: Tuple[int, int] = (200, 1241),
    side_size: Tuple[int, int] = (400, 1241)
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """预处理图片：检查并裁剪到指定大小"""

    def resize_to_target(images: List[np.ndarray], target_w: int, target_h: int, label: str):
        processed = []
        for i, img in enumerate(images):
            h, w = img.shape[:2]
            if w == target_w and h == target_h:
                processed.append(img)
            else:
                if w < target_w or h < target_h:
                    print(f"  [警告] {label} 图片 {i} ({w}x{h}) 小于目标尺寸 ({target_w}x{target_h})，将进行放大处理")
                    img_resized = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
                    processed.append(img_resized)
                else:
                    x_start = (w - target_w) // 2
                    y_start = (h - target_h) // 2
                    img_cropped = img[y_start:y_start + target_h, x_start:x_start + target_w]
                    processed.append(img_cropped)
        return processed

    processed_center = resize_to_target(center_images, center_size[0], center_size[1], "Center")
    processed_side = resize_to_target(side_images, side_size[0], side_size[1], "Side")

    return processed_center, processed_side


def generate_layout_images(
    center_images: List[np.ndarray],
    side_images: List[np.ndarray],
    rib_count: int,
    symmetry_type: str = "random"
) -> List[LayoutResult]:
    """生成轮胎花纹布局图"""
    center_images, side_images = preprocess_images(center_images, side_images)

    results = []

    manager = CombinationManager(center_images, side_images, rib_count)

    valid_modes = ["asymmetric", "rotate180", "mirror", "mirror_shifted"]
    all_symmetry_modes = ["rotate180", "mirror", "mirror_shifted"]

    if symmetry_type == "random":
        modes_to_generate = [random.choice(["asymmetric"] + all_symmetry_modes)]
    elif symmetry_type == "both":
        modes_to_generate = ["asymmetric"] + all_symmetry_modes
    elif symmetry_type == "all_symmetry":
        modes_to_generate = all_symmetry_modes
    elif symmetry_type in valid_modes:
        modes_to_generate = [symmetry_type]
    else:
        modes_to_generate = ["asymmetric"]

    for mode_type in modes_to_generate:
        is_asymmetric = (mode_type == "asymmetric")

        if is_asymmetric:
            selected_combinations = manager.select_combinations_by_priority("asymmetric")
        else:
            selected_combinations = manager.select_combinations_by_priority("symmetry")

        for combo in selected_combinations:
            if is_asymmetric:
                ribs = []
                if rib_count == 5:
                    ribs = [
                        side_images[combo[0]],
                        center_images[combo[1]],
                        center_images[combo[2]],
                        center_images[combo[3]],
                        side_images[combo[4]]
                    ]
                else:  # 4 RIB 模式
                    ribs = [
                        side_images[combo[0]],
                        center_images[combo[1]],
                        center_images[combo[2]],
                        side_images[combo[3]]
                    ]
            else:
                if rib_count == 5:
                    full_combo = (0, 0, combo[0], combo[1], combo[2])
                    initial_ribs = [
                        side_images[0],
                        center_images[0],
                        center_images[combo[0]],
                        center_images[combo[1]],
                        side_images[combo[2]]
                    ]
                else:  # 4 RIB 模式
                    full_combo = (0, 0, combo[0], combo[1])
                    initial_ribs = [
                        side_images[0],
                        center_images[0],
                        center_images[combo[0]],
                        side_images[combo[1]]
                    ]
                ribs = apply_symmetry_coverage(initial_ribs, rib_count, mode_type)
                combo = full_combo

            groove_positions = [[100, 300, 500, 700]] * rib_count
            side_rib_indices = [0, rib_count - 1] if rib_count > 0 else []

            result = assemble_symmetry_layout(
                extracted_ribs=ribs,
                user_config={"symmetry_type": mode_type},
                groove_positions=groove_positions,
                rib_combination=combo,
                side_rib_indices=side_rib_indices
            )
            results.append(result)

    return results


def save_results(results: List[LayoutResult], output_dir: str = None):
    """保存结果到指定目录"""
    if output_dir is None:
        output_dir = CONFIG.get('paths', {}).get('output_dir')

    os.makedirs(output_dir, exist_ok=True)

    sym_dict = CONFIG.get('symmetry_mapping', {
        "asymmetric": 0,
        "rotate180": 1,
        "mirror": 2,
        "mirror_shifted": 3
    })

    for idx, result in enumerate(results):
        sym_number = sym_dict.get(result.applied_symmetry, 99)

        rib_combination = result.rib_combination or ()
        combo_len = len(rib_combination)
        rib_count = len(result.rib_regions)

        if combo_len == 5:
            combo_str = (
                f"r1_{rib_combination[0]}_"
                f"r2_{rib_combination[1]}_"
                f"r3_{rib_combination[2]}_"
                f"r4_{rib_combination[3]}_"
                f"r5_{rib_combination[4]}"
            )
        elif combo_len == 4:
            combo_str = (
                f"r1_{rib_combination[0]}_"
                f"r2_{rib_combination[1]}_"
                f"r3_{rib_combination[2]}_"
                f"r4_{rib_combination[3]}"
            )
        elif combo_len == 3 and rib_count == 5:
            combo_str = (
                f"r3_{rib_combination[0]}_"
                f"r4_{rib_combination[1]}_"
                f"r5_{rib_combination[2]}"
            )
        elif combo_len == 2 and rib_count == 4:
            combo_str = (
                f"r3_{rib_combination[0]}_"
                f"r4_{rib_combination[1]}"
            )
        else:
            combo_str = "combo_" + "_".join(str(x) for x in rib_combination)

        out_filename = f"sym_{sym_number}_{combo_str}.png"
        out_path = os.path.join(output_dir, out_filename)

        cv2.imwrite(out_path, result.layout_image)
        print(f"  -> 成功! 保存至 {out_filename} [得分: {result.layout_score}]")
