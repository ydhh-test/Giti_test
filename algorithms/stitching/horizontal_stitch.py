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
    config: Dict[str, Any],
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

    【输入参数】
    - extracted_ribs (List[np.ndarray]): 已经切分好的各条 RIB 图像数组，顺序从左到右 (例如 [part1, part2, part3, part4, part5])。
    - user_config (Dict[str, Any]): 用户配置字典。必须包含:
        - "symmetry_type" (str): 对称类型，可选值包含 "asymmetric", "rotate180", "mirror", "mirror_shifted", 或 "random"。
    - groove_positions (List[List[int]]): 包含各个 RIB 内部横沟/钢片中心点在 Y 轴的像素坐标列表。用于计算平均节距。
    - rib_combination (Tuple): 使用的 RIB 组合索引。
    - blend_width (int, 可选): 边缘融合的像素宽度，默认 10 像素。
    - side_rib_indices (List[int], 可选): 来自 side 目录的 RIB 索引列表（如 [0, 4] 表示第1和第5个RIB来自side）。若不传，则所有 RIB 统一宽度裁剪。

    【输出返回】
    - LayoutResult: 包含生成图像、实际应用的对称类型、错位偏移量、RIB 边界坐标以及质量得分的命名元组。
    """

    if side_rib_indices is None:
        side_rib_indices = []

    # 使用配置中的默认值
    if blend_width is None:
        blend_width = config.get('blend_width', 10)
    main_groove_width = config.get('main_groove_width', 20)

    # ==========================================
    # 1. 防御性检查与高度对齐（按本组最小高度裁剪，不做缩放/补边）
    # ==========================================
    if not extracted_ribs:
        raise ValueError("输入异常: 提取的 RIB 列表不能为空。")

    # 以当前组合中“高度最小的那条 RIB”为基准高度
    target_h = min(rib.shape[0] for rib in extracted_ribs)

    normalized_ribs = []
    for rib in extracted_ribs:
        h, w, c = rib.shape

        if h == target_h:
            # 高度刚好，直接使用
            normalized_ribs.append(rib)
        else:
            # 仅做裁剪，不做缩放：从中间截取一段 target_h 高度
            y_start = (h - target_h) // 2
            y_end = y_start + target_h
            cropped = rib[y_start:y_end, :, :]
            normalized_ribs.append(cropped)

    extracted_ribs = normalized_ribs
    img_h = target_h

    # 在高度统一后，再统一每条 RIB 的宽度：
    # - 来自 side 的 RIB（两边的）保持原始宽度，不裁剪
    # - 来自 center 的 RIB（中间的）按本组最小宽度居中裁剪
    # 只对非 side 区域的 RIB 计算最小宽度
    non_side_ribs = [rib for i, rib in enumerate(extracted_ribs) if i not in side_rib_indices]
    if non_side_ribs:
        target_w = min(rib.shape[1] for rib in non_side_ribs)
    else:
        # 如果全是 side RIB，则取最小的宽度
        target_w = min(rib.shape[1] for rib in extracted_ribs)

    if target_w <= 0 or target_h <= 0:
        raise ValueError(
            f"输入异常: 归一化后 RIB 尺寸无效 (target_h={target_h}, target_w={target_w})，请检查输入图片尺寸。"
        )

    normalized_width_ribs = []
    for i, rib in enumerate(extracted_ribs):
        h, w, c = rib.shape
        # 如果是 side RIB，保持原始宽度不裁剪
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
    main_groove_count = num_ribs - 1  # 物理规律：主沟数 = RIB 数 - 1


    # ==========================================
    # 2. 基础非对称拼接与 Alpha 渐变边缘融合
    # ==========================================
    # 计算目标画布所需总宽度 = 所有RIB实际切出来的宽度之和 + 所有主沟占用的预留宽度
    total_rib_width = sum(rib.shape[1] for rib in extracted_ribs)
    total_layout_width = total_rib_width + (main_groove_count * main_groove_width)

    # 初始化纯黑画布，黑色背景代表未填充的主沟区域
    layout_img = np.zeros((img_h, total_layout_width, 3), dtype=np.uint8)
    current_x = 0
    rib_regions = []

    def apply_edge_blend(img: np.ndarray, bw: int, is_first: bool, is_last: bool) -> np.ndarray:
        """
        【内部辅助函数：边缘平滑融合】
        - 功能：在给定的图像片段（RIB）边缘应用从 1.0 到 0.0 的 Alpha 线性衰减，让硬切缝融入黑底主沟。
        - 逻辑：构建一个与图像同尺寸的 Float32 掩码矩阵，利用 NumPy 广播对边缘列赋予渐变系数，最后与原图点乘。
        - 参数：
            - img: 要处理的单条 RIB 图像。
            - bw (int): blend_width，渐变过渡区的像素宽度。
            - is_first (bool): 是否是全局最左侧的 RIB 1（若是，则左边缘不作融合）。
            - is_last (bool): 是否是全局最右侧的最后一条 RIB（若是，则右边缘不作融合）。
        - 返回：经过边缘衰减处理后的图像片段。
        """
        h, w, c = img.shape
        # 防御性判断：如果 RIB 太窄，容不下左右两个融合宽度，直接返回原图避免越界崩溃
        if w <= 2 * bw:
            return img

        # 初始化一个 1xWx1 的常数 1 矩阵（利用广播机制，省去了申请 HxWx1 的大内存）
        mask = np.ones((1, w, 1), dtype=np.float32)

        if not is_first:
            # 左边缘需要向左边的主沟淡入：从 0(纯黑) 线性增加到 1(原色)
            mask[:, :bw, :] = np.linspace(0.0, 1.0, bw).reshape(1, bw, 1)
        if not is_last:
            # 右边缘需要向右边的主沟淡出：从 1(原色) 线性衰减到 0(纯黑)
            mask[:, -bw:, :] = np.linspace(1.0, 0.0, bw).reshape(1, bw, 1)

        # img 提权为 float32 与 mask 相乘，再安全降级回 uint8
        return (img.astype(np.float32) * mask).astype(np.uint8)

    # 遍历拼合提取出的 RIB
    for i, rib in enumerate(extracted_ribs):
        is_first_rib = (i == 0)
        is_last_rib = (i == num_ribs - 1)

        # 先对当前 RIB 执行边缘渐变
        blended_rib = apply_edge_blend(rib, blend_width, is_first_rib, is_last_rib)

        rib_w = blended_rib.shape[1]
        x_end = current_x + rib_w

        # 将处理好的 RIB 贴入全局画布
        layout_img[:, current_x:x_end] = blended_rib
        rib_regions.append((current_x, 0, x_end, img_h))

        # 更新 X 坐标指针：跳过已绘制的 RIB 和一条主沟的宽度，为下一个 RIB 寻找起点
        current_x = x_end + main_groove_width


    # ==========================================
    # 3. 动态计算平均节距 (Pitch) 决定平移量
    # ==========================================
    # 逻辑：遍历所有 RIB 内所有的横沟 Y 坐标，计算相邻横沟的差值，求全体平均数即为 Pitch。
    pitch_diffs = []
    for rib_grooves in groove_positions:
        if len(rib_grooves) > 1:
            # np.diff 计算列表相邻元素的差值 [a2-a1, a3-a2...]
            pitch_diffs.extend(np.diff(rib_grooves))

    avg_pitch = np.mean(pitch_diffs) if pitch_diffs else 0.0
    # 物理要求：错位效果一般为横沟均分，即平移量刚好是节距的一半
    shift_offset = avg_pitch / 2.0


    # ==========================================
    # 4. 全局几何变换与对称路由 (核心架构)
    # ==========================================
    # 逻辑：采用"后处理架构"——不对单个 RIB 做变换，而是将拼接好的非对称全图一刀切开，
    # 拿右半幅图像进行矩阵变换，再贴回左半幅。这样天然处理了中心 RIB 的内部对称。

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
        # 寻找全局图像中轴线
        mid_x = total_layout_width // 2
        right_half_w = total_layout_width - mid_x
        left_half_w = mid_x  # 左半幅宽度

        # 抠出右半边图像作为变换基底 (必须 .copy() 以防视图引用问题)
        right_half = layout_img[:, mid_x: total_layout_width].copy()

        if symmetry_mode == "rotate180":
            # 旋转180°策略: 相当于同时水平翻转(X轴)和垂直翻转(Y轴)
            transformed_half = cv2.rotate(right_half, cv2.ROTATE_180)

        elif symmetry_mode == "mirror":
            # 镜像对称策略: 仅作水平翻转 (X轴)
            transformed_half = cv2.flip(right_half, 1)

        elif symmetry_mode == "mirror_shifted":
            # 镜像错位策略: 先水平翻转，再利用 np.roll 进行 Y 轴纵向环绕平移 (Wrap-around)
            mirrored = cv2.flip(right_half, 1)
            # np.roll 实现完美的圆周循环补齐，超出边界的像素自动卷到另一侧
            transformed_half = np.roll(mirrored, shift=int(shift_offset), axis=0)

        # 将变换后的右半幅覆写回左半幅，保证左右宽度一致，避免 broadcast 报错
        copy_w = min(left_half_w, right_half_w)
        if copy_w > 0:
            left_start = mid_x - copy_w
            layout_img[:, left_start:mid_x] = transformed_half[:, :copy_w]


    # ==========================================
    # 5. 质量评估与组装返回
    # ==========================================
    # 量化评分逻辑：
    # 基础分 8 分：当前只要生成了一条符合物理对称性原则（或合法定义为不对称）的有效轮胎切片，即获得 8 分。
    base_score = 8.0
    # 额外匹配分 1 分：如果本次成功应用的对称效果（applied_symmetry）与用户在配置里明确指定的意图（非 random 盲盒）精准一致，则额外 +1 分。
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


# ==========================================
# 全排列组合管理
# ==========================================
class CombinationManager:
    """全排列组合管理器"""

    def __init__(self, center_images: List, side_images: List, rib_count: int, config: dict):
        self.center_images = center_images
        self.side_images = side_images
        self.rib_count = rib_count
        self.config = config

        # 历史计数文件路径 - 从 config 中获取，不设置默认值（避免 hard code）
        history_path = self.config.get('history_file')
        if history_path:
            # 如果是相对路径，转换为绝对路径
            history_path = Path(history_path)
            if not history_path.is_absolute():
                history_path = Path.cwd() / history_path
            self.history_file = str(history_path)
        else:
            # 如果没有传入 history_file，则不启用历史计数功能
            self.history_file = None

        # 加载历史计数
        self.history_counts = self._load_history()

        # 生成全排列组合
        self.asymmetric_combinations = self._generate_asymmetric_combinations()
        self.symmetry_combinations = self._generate_symmetry_combinations()

    def _load_history(self) -> Dict:
        """加载历史计数"""
        if self.history_file is None:
            return defaultdict(int)
        if Path(self.history_file).exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return defaultdict(int)
        return defaultdict(int)

    def _save_history(self):
        """保存历史计数"""
        if self.history_file is None:
            return
        history_path = Path(self.history_file)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(dict(self.history_counts), f, ensure_ascii=False, indent=2)

    def _generate_asymmetric_combinations(self) -> List[Tuple]:
        """
        生成不对称模式的全排列组合
        5 RIB: RIB1,5 来自 side (可重复), RIB2,3,4 来自 center (可重复)
        4 RIB: RIB1,4 来自 side (可重复), RIB2,3 来自 center (可重复)
        """
        side_indices = list(range(len(self.side_images)))
        center_indices = list(range(len(self.center_images)))

        if self.rib_count == 5:
            # RIB1, RIB5 -> side; RIB2, RIB3, RIB4 -> center
            # 允许重复使用，所以使用 product
            side_combinations = list(product(side_indices, repeat=2))  # (RIB1, RIB5)
            center_combinations = list(product(center_indices, repeat=3))  # (RIB2, RIB3, RIB4)

            combinations = []
            for side_combo in side_combinations:
                for center_combo in center_combinations:
                    # (RIB1, RIB2, RIB3, RIB4, RIB5)
                    combinations.append((side_combo[0], center_combo[0], center_combo[1], center_combo[2], side_combo[1]))
        else:
            # 4 RIB: RIB1, RIB4 -> side; RIB2, RIB3 -> center
            side_combinations = list(product(side_indices, repeat=2))  # (RIB1, RIB4)
            center_combinations = list(product(center_indices, repeat=2))  # (RIB2, RIB3)

            combinations = []
            for side_combo in side_combinations:
                for center_combo in center_combinations:
                    # (RIB1, RIB2, RIB3, RIB4)
                    combinations.append((side_combo[0], center_combo[0], center_combo[1], side_combo[1]))

        return combinations

    def _generate_symmetry_combinations(self) -> List[Tuple]:
        """
        生成对称模式下的组合（使用右半部分覆盖左半部分策略）
        5 RIB: 只排列 RIB3, RIB4, RIB5（右侧3个位置），RIB1, RIB2 由覆盖生成
        4 RIB: 只排列 RIB3, RIB4（右侧2个位置），RIB1, RIB2 由覆盖生成

        覆盖逻辑：
        - 5 RIB: 将 RIB4, RIB5 的图像覆盖到 RIB1, RIB2 的位置，RIB3 保持不变
        - 4 RIB: 将 RIB3, RIB4 的图像覆盖到 RIB1, RIB2 的位置
        """
        center_indices = list(range(len(self.center_images)))
        side_indices = list(range(len(self.side_images)))

        if self.rib_count == 5:
            # 5 RIB: RIB3 来自 center, RIB4, RIB5 来自 center/side
            # 覆盖策略：RIB4 -> RIB2, RIB5 -> RIB1
            # 组合: (RIB3, RIB4, RIB5)
            combinations = []
            for rib3_idx in center_indices:
                for rib4_idx in center_indices:
                    for rib5_idx in side_indices:
                        # (RIB3, RIB4, RIB5) - 对应实际位置 RIB3, RIB4, RIB5
                        combinations.append((rib3_idx, rib4_idx, rib5_idx))
        else:
            # 4 RIB: RIB3 来自 center, RIB4 来自 side
            # 覆盖策略：RIB4 -> RIB2, RIB3 -> RIB1
            # 组合: (RIB3, RIB4)
            combinations = []
            for rib3_idx in center_indices:
                for rib4_idx in side_indices:
                    combinations.append((rib3_idx, rib4_idx))

        return combinations

    def _get_combo_key(self, combo: Tuple, mode: str) -> str:
        """获取组合的唯一键值"""
        return f"{mode}_{combo}"

    def select_combinations_by_priority(self, mode: str, count: int = None) -> List[Tuple]:
        """
        根据历史计数选择优先使用计数少的组合

        Args:
            mode: 'asymmetric' 或 'symmetry'
            count: 需要选择的数量，默认取配置的最大值

        Returns:
            选中的组合列表
        """
        if count is None:
            count = self.config.get('generation', {}).get('max_per_mode', 10)

        if mode == 'asymmetric':
            combinations = self.asymmetric_combinations
        else:
            combinations = self.symmetry_combinations

        if not combinations:
            return []

        # 获取所有组合的计数
        combo_with_counts = []
        for combo in combinations:
            key = self._get_combo_key(combo, mode)
            cnt = self.history_counts.get(key, 0)
            combo_with_counts.append((combo, cnt))

        # 按计数升序排序（计数少的优先）
        combo_with_counts.sort(key=lambda x: x[1])

        # 选择前 count 个
        selected = [combo for combo, _ in combo_with_counts[:count]]

        # 更新计数（键可能尚未存在，用 get 避免 KeyError）
        for combo in selected:
            key = self._get_combo_key(combo, mode)
            self.history_counts[key] = self.history_counts.get(key, 0) + 1

        # 保存历史计数
        self._save_history()

        return selected


# ==========================================
# 数据读取与处理
# ==========================================
def load_images_from_directories(config: Dict[str, Any]) -> Tuple[List, List, Dict]:
    """
    从 center 和 side 目录读取所有图片，按来源重命名

    Returns:
        center_images: center 目录的图片列表
        side_images: side 目录的图片列表
        image_names: 记录图片来源的字典 {'center_0': '原始文件名', 'side_0': '原始文件名'}
    """
    center_dir = config.get('center_dir')
    side_dir = config.get('side_dir')

    center_images = []
    side_images = []
    image_names = {}

    # 读取 center 目录
    if os.path.exists(center_dir):
        for idx, filename in enumerate(sorted(os.listdir(center_dir))):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                img_path = os.path.join(center_dir, filename)
                img = cv2.imread(img_path)
                if img is not None:
                    center_images.append(img)
                    image_names[f'center_{idx}'] = filename

    # 读取 side 目录
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
    """
    应用对称覆盖策略

    5 RIB: 将 RIB4, RIB5 的图像覆盖到 RIB1, RIB2 的位置，RIB3 保持不变
    4 RIB: 将 RIB3, RIB4 的图像覆盖到 RIB1, RIB2 的位置

    Args:
        ribs: 原始 RIB 列表 [RIB1, RIB2, RIB3, RIB4, RIB5] 或 [RIB1, RIB2, RIB3, RIB4]
        rib_count: RIB 数量
        symmetry_mode: 对称模式

    Returns:
        覆盖后的 RIB 列表
    """
    if symmetry_mode == 'asymmetric':
        return ribs

    result = list(ribs)  # 复制一份

    if rib_count == 5:
        # 5 RIB: RIB4 -> RIB2, RIB5 -> RIB1
        # 注意：RIB 索引从 0 开始
        # RIB1=index0, RIB2=index1, RIB3=index2, RIB4=index3, RIB5=index4
        result[1] = ribs[3].copy()  # RIB2 <- RIB4
        result[0] = ribs[4].copy()  # RIB1 <- RIB5
        # RIB3 (index2) 保持不变
    else:
        # 4 RIB: RIB3 -> RIB1, RIB4 -> RIB2
        # RIB1=index0, RIB2=index1, RIB3=index2, RIB4=index3
        result[0] = ribs[2].copy()  # RIB1 <- RIB3
        result[1] = ribs[3].copy()  # RIB2 <- RIB4
        # RIB3 (index2) 保持不变

    return result


def preprocess_images(
    center_images: List[np.ndarray],
    side_images: List[np.ndarray],
    center_size: Tuple[int, int] = (200, 1241),
    side_size: Tuple[int, int] = (400, 1241)
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    预处理图片：检查并裁剪到指定大小

    Args:
        center_images: center 目录的图片列表
        side_images: side 目录的图片列表
        center_size: center 图片的目标尺寸 (宽, 高)
        side_size: side 图片的目标尺寸 (宽, 高)

    Returns:
        处理后的 (center_images, side_images)
    """
    def resize_to_target(images: List[np.ndarray], target_w: int, target_h: int, label: str):
        processed = []
        for i, img in enumerate(images):
            h, w = img.shape[:2]
            if w == target_w and h == target_h:
                processed.append(img)
            else:
                if w < target_w or h < target_h:
                    print(f"  [警告] {label} 图片 {i} ({w}x{h}) 小于目标尺寸 ({target_w}x{target_h})，将进行放大处理")
                    # 放大：使用插值
                    img_resized = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
                    processed.append(img_resized)
                else:
                    # 裁剪：居中裁剪到目标尺寸
                    x_start = (w - target_w) // 2
                    y_start = (h - target_h) // 2
                    img_cropped = img[y_start:y_start + target_h, x_start:x_start + target_w]
                    processed.append(img_cropped)
        return processed

    print(f"\n[预处理] 检查图片尺寸...")
    print(f"  - Center 图片目标尺寸: {center_size[0]}x{center_size[1]} (宽x高)")
    print(f"  - Side 图片目标尺寸: {side_size[0]}x{side_size[1]} (宽x高)")

    processed_center = resize_to_target(center_images, center_size[0], center_size[1], "Center")
    processed_side = resize_to_target(side_images, side_size[0], side_size[1], "Side")

    return processed_center, processed_side


def generate_layout_images(
    center_images: List[np.ndarray],
    side_images: List[np.ndarray],
    rib_count: int,
    config: Dict[str, Any],
    symmetry_type: str = "random"
) -> List[LayoutResult]:
    """
    生成轮胎花纹布局图

    Args:
        center_images: center 目录的图片列表
        side_images: side 目录的图片列表
        rib_count: RIB 数量 (4 或 5)
        config: 配置字典
        symmetry_type: 对称类型，可选值:
            - "asymmetric": 仅非对称模式
            - "rotate180": 仅旋转180°对称
            - "mirror": 仅镜像对称
            - "mirror_shifted": 仅镜像错位对称
            - "all_symmetry": 所有对称模式(rotate180/mirror/mirror_shifted)都生成
            - "both": 非对称 + 所有对称模式都生成
            - "random": 随机选择一种模式

    Returns:
        布局结果列表
    """
    # 预处理图片：检查并裁剪到指定大小
    center_images, side_images = preprocess_images(center_images, side_images)

    results = []

    # 创建组合管理器
    manager = CombinationManager(center_images, side_images, rib_count, config)

    # 解析模式，确定要生成的模式列表
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

    print(f"\n[模式] 将生成以下模式: {modes_to_generate}")

    # 遍历每种模式生成图片
    for mode_type in modes_to_generate:
        is_asymmetric = (mode_type == "asymmetric")

        if is_asymmetric:
            # 不对称模式：使用所有 RIB 排列组合
            selected_combinations = manager.select_combinations_by_priority("asymmetric")
        else:
            # 对称模式：只排列右侧 RIB，使用覆盖策略
            selected_combinations = manager.select_combinations_by_priority("symmetry")

        for combo in selected_combinations:
            if is_asymmetric:
                # 不对称模式：直接使用组合的 RIB
                ribs = []
                if rib_count == 5:
                    # combo: (RIB1_idx, RIB2_idx, RIB3_idx, RIB4_idx, RIB5_idx)
                    ribs = [
                        side_images[combo[0]],  # RIB1 from side
                        center_images[combo[1]],  # RIB2 from center
                        center_images[combo[2]],  # RIB3 from center
                        center_images[combo[3]],  # RIB4 from center
                        side_images[combo[4]]  # RIB5 from side
                    ]
                else:
                    # combo: (RIB1_idx, RIB2_idx, RIB3_idx, RIB4_idx)
                    ribs = [
                        side_images[combo[0]],  # RIB1 from side
                        center_images[combo[1]],  # RIB2 from center
                        center_images[combo[2]],  # RIB3 from center
                        side_images[combo[3]]  # RIB4 from side
                    ]
            else:
                # 对称模式：只排列右侧 RIB，使用覆盖策略
                if rib_count == 5:
                    # combo: (RIB3_idx, RIB4_idx, RIB5_idx)
                    # 初始右侧 RIB: RIB3, RIB4, RIB5
                    # 使用 combo 中的索引来构建完整的组合，用于命名
                    # 假设 RIB1, RIB2 使用 center_images[0] (第0张)
                    full_combo = (0, 0, combo[0], combo[1], combo[2])  # 完整5RIB组合
                    initial_ribs = [
                        side_images[0],  # RIB1 (会被覆盖)
                        center_images[0],  # RIB2 (会被覆盖)
                        center_images[combo[0]],  # RIB3 (保持不变)
                        center_images[combo[1]],  # RIB4
                        side_images[combo[2]]  # RIB5
                    ]
                else:
                    # combo: (RIB3_idx, RIB4_idx)
                    # 假设 RIB1, RIB2 使用 center_images[0]
                    full_combo = (0, 0, combo[0], combo[1])  # 完整4RIB组合
                    initial_ribs = [
                        side_images[0],  # RIB1 (会被覆盖)
                        center_images[0],  # RIB2 (会被覆盖)
                        center_images[combo[0]],  # RIB3 (会被覆盖)
                        side_images[combo[1]]  # RIB4
                    ]
                # 应用覆盖策略
                ribs = apply_symmetry_coverage(initial_ribs, rib_count, mode_type)
                # 使用完整组合替换原来的部分组合
                combo = full_combo

            # 模拟横沟坐标
            groove_positions = [[100, 300, 500, 700]] * rib_count

            # side RIB 索引：5 RIB 时为 [0, 4]，4 RIB 时为 [0, 3]
            side_rib_indices = [0, rib_count - 1] if rib_count > 0 else []

            # 执行拼接
            result = assemble_symmetry_layout(
                extracted_ribs=ribs,
                user_config={"symmetry_type": mode_type},
                groove_positions=groove_positions,
                config=config,
                rib_combination=combo,
                side_rib_indices=side_rib_indices
            )
            results.append(result)

    return results


def save_results(results: List[LayoutResult], config: Dict[str, Any], output_dir: str = None) -> List[Dict[str, Any]]:
    """
    保存结果到指定目录

    Returns:
        List[Dict[str, Any]]: 保存的图片信息列表，每个包含 filename, output_path, symmetry, score
    """
    if output_dir is None:
        output_dir = config.get('output_dir')

    os.makedirs(output_dir, exist_ok=True)

    # 对称模式映射
    sym_dict = config.get('symmetry_mapping', {
        "asymmetric": 0,
        "rotate180": 1,
        "mirror": 2,
        "mirror_shifted": 3
    })

    # 收集保存的图片信息
    saved_images = []

    for idx, result in enumerate(results):
        sym_number = sym_dict.get(result.applied_symmetry, 99)

        # 生成文件名：根据 rib_combination 的长度自适应，避免索引越界
        rib_combination = result.rib_combination or ()
        combo_len = len(rib_combination)
        rib_count = len(result.rib_regions)  # 实际参与拼接的 RIB 数

        if combo_len == 5:
            # 5 RIB 完整组合：r1_side, r2_center, r3_center, r4_center, r5_side
            combo_str = (
                f"r1_{rib_combination[0]}_"
                f"r2_{rib_combination[1]}_"
                f"r3_{rib_combination[2]}_"
                f"r4_{rib_combination[3]}_"
                f"r5_{rib_combination[4]}"
            )
        elif combo_len == 4:
            # 4 RIB 完整组合：r1_side, r2_center, r3_center, r4_side
            combo_str = (
                f"r1_{rib_combination[0]}_"
                f"r2_{rib_combination[1]}_"
                f"r3_{rib_combination[2]}_"
                f"r4_{rib_combination[3]}"
            )
        elif combo_len == 3 and rib_count == 5:
            # 对称模式 5 RIB: 只排列 r3, r4, r5
            combo_str = (
                f"r3_{rib_combination[0]}_"
                f"r4_{rib_combination[1]}_"
                f"r5_{rib_combination[2]}"
            )
        elif combo_len == 2 and rib_count == 4:
            # 对称模式 4 RIB: 只排列 r3, r4
            combo_str = (
                f"r3_{rib_combination[0]}_"
                f"r4_{rib_combination[1]}"
            )
        else:
            # 兜底：直接把组合 tuple 展平到字符串
            combo_str = "combo_" + "_".join(str(x) for x in rib_combination)

        out_filename = f"sym_{sym_number}_{combo_str}.png"
        out_path = os.path.join(output_dir, out_filename)

        cv2.imwrite(out_path, result.layout_image)
        print(f"  -> 成功！保存至 {out_filename} [得分：{result.layout_score}]")

        # 收集图片信息
        saved_images.append({
            "filename": out_filename,
            "output_path": out_path,
            "symmetry": result.applied_symmetry,
            "score": result.layout_score
        })

    return saved_images




# ==========================================
# 横图拼接主类
# ==========================================
class HorizontalStitch:
    """
    横图拼接算法类
    
    功能:
    - 从指定目录加载RIB图片
    - 根据配置生成多种对称模式的横向布局
    - 支持批量生成和单次拼接
    
    使用方式:
        stitcher = HorizontalStitch(task_id, conf)
        flag, details = stitcher.process()
    """
    
    def __init__(self, task_id: str, conf: dict):
        """
        初始化横图拼接器
        
        Args:
            task_id: 任务ID
            conf: 配置字典,包含:
                - rib_count: RIB数量 (4或5)
                - symmetry_type: 对称类型
                - center_dir: 中间RIB目录
                - side_dir: 边缘RIB目录
                - output_dir: 输出目录
                - max_per_mode: 每种模式最大生成数
                - blend_width: 边缘融合宽度
                - main_groove_width: 主沟宽度
        """
        self.task_id = task_id
        self.conf = conf
        
        # 提取配置参数
        self.rib_count = conf.get('rib_count', 5)
        self.symmetry_type = conf.get('symmetry_type', 'asymmetric')
        
        # 初始化状态
        self.center_images = []
        self.side_images = []
        self.image_names = {}
        self.results = []
    
    def process(self) -> Tuple[bool, dict]:
        """
        主处理流程
        
        Returns:
            (flag, details): 
                - flag: 是否成功
                - details: 详细信息,包含生成的图片数量、路径等
        """
        try:
            # 1. 加载图片
            self.center_images, self.side_images, self.image_names = load_images_from_directories(self.conf)
            
            if not self.center_images or not self.side_images:
                return False, {
                    "error": "图片加载失败",
                    "center_count": len(self.center_images),
                    "side_count": len(self.side_images)
                }
            
            # 2. 生成布局图
            self.results = generate_layout_images(
                self.center_images,
                self.side_images,
                self.rib_count,
                self.conf,
                self.symmetry_type
            )
            
            if not self.results:
                return False, {"error": "未生成任何布局图"}
            
            # 3. 保存结果，获取图片列表
            saved_images = save_results(self.results, self.conf)
            
            # 4. 返回成功信息（包含图片列表）
            return True, {
                "generated_count": len(self.results),
                "symmetry_types": list(set(r.applied_symmetry for r in self.results)),
                "average_score": sum(r.layout_score for r in self.results) / len(self.results),
                "images": saved_images
            }
            
        except Exception as e:
            return False, {"error": str(e)}
