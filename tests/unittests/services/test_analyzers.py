import pytest
import numpy as np
import cv2
import os
from services.analyzers import compute_land_sea_ratio, compute_black_area, compute_gray_area

# ==========================================
# 0. 测试数据路径配置 (全局变量，方便统一管理)
# ==========================================
# 使用相对于测试文件的路径
# 文件位置: tests/unittests/services/test_analyzers.py
# 数据位置: tests/datasets/test_data_land_sea/
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets", "test_data_land_sea")
IMG_PATH_SCORE_2 = os.path.join(TEST_DATA_DIR, "2分.png")
# IMG_PATH_SCORE_1 = os.path.join(TEST_DATA_DIR, "1分.png")
ALL_WHITE_0 = os.path.join(TEST_DATA_DIR, "all_white.png")
MUCH_BLACK_0 = os.path.join(TEST_DATA_DIR, "much_blackLine.png")

# ==========================================
# 1. 基础配置：使用 pytest.fixture 提供全局变量
# ==========================================
@pytest.fixture
def default_conf():
    """提供测试用的标准评分配置"""
    return {
        "target_min": 28.0,
        "target_max": 35.0,
        "margin": 5.0
    }

# ==========================================
# 2. 测试面积计算子函数
# ==========================================
def test_compute_black_area():
    img = np.full((10, 10), 255, dtype=np.uint8)
    img[0:3, 0:5] = 0
    assert compute_black_area(img) == 15

def test_compute_gray_area():
    img = np.full((10, 10), 255, dtype=np.uint8)
    img[0:5, 0:5] = 100
    assert compute_gray_area(img) == 25

# ==========================================
# 3. 测试核心打分逻辑 (满分 2 分)
# ==========================================
def test_compute_land_sea_ratio_score_2_real_image(default_conf):
    """测试满分情况：读取真实的 2 分业务图片，并将特征区域染色保存"""
    img = cv2.imdecode(np.fromfile(IMG_PATH_SCORE_2, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert img is not None, f"错误：无法读取测试图片，请检查路径 -> {IMG_PATH_SCORE_2}"

    score, details = compute_land_sea_ratio(img, default_conf)
    print(f"\n[真实图片测试] 海陆比: {details['ratio_value']}%, 应该得分: 2, 实际得分: {score}")

    # 染色与保存逻辑
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    black_mask = cv2.inRange(gray, 0, 50)
    gray_mask = cv2.inRange(gray, 50, 200)

    vis_img = img.copy()
    vis_img[black_mask > 0] = (0, 255, 0)
    vis_img[gray_mask > 0] = (0, 0, 255)

    # 输出目录：相对于测试文件所在目录
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets", "test_data_land_sea_visual")
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.basename(IMG_PATH_SCORE_2)
    save_path = os.path.join(output_dir, f"visual_{filename}")

    is_success, buffer = cv2.imencode(".png", vis_img)
    if is_success:
        buffer.tofile(save_path)
        print(f" -> 可视化染色图已保存至: {save_path}")
    else:
        print(f" -> 警告：可视化图片保存失败！")

    assert score == 2, f"图片海陆比为 {details['ratio_value']}%，不符合 2 分标准"

# ==========================================
# 4. 测试容错打分逻辑 (得 1 分) ***********暂无明确测试用例***********
# ==========================================
# def test_compute_land_sea_ratio_score_1_real_image(default_conf):
#     """测试容错情况：读取真实的 1 分业务图片，并将特征区域染色保存"""
#     img = cv2.imdecode(np.fromfile(IMG_PATH_SCORE_1, dtype=np.uint8), cv2.IMREAD_COLOR)
#     assert img is not None, f"错误：无法读取测试图片，请检查路径 -> {IMG_PATH_SCORE_1}"
#
#     score, details = compute_land_sea_ratio(img, default_conf)
#     print(f"\n[真实图片测试] 海陆比: {details['ratio_value']}%, 应该得分: 1, 实际得分: {score}")
#
#     # 染色与保存逻辑
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     black_mask = cv2.inRange(gray, 0, 50)
#     gray_mask = cv2.inRange(gray, 50, 200)
#
#     vis_img = img.copy()
#     vis_img[black_mask > 0] = (0, 255, 0)
#     vis_img[gray_mask > 0] = (0, 0, 255)
#
    #     output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets", "test_data_land_sea_visual")
#     os.makedirs(output_dir, exist_ok=True)
#
#     filename = os.path.basename(IMG_PATH_SCORE_1)
#     save_path = os.path.join(output_dir, f"visual_{filename}")
#
#     is_success, buffer = cv2.imencode(".png", vis_img)
#     if is_success:
#         buffer.tofile(save_path)
#         print(f" -> 可视化染色图已保存至: {save_path}")
#     else:
#         print(f" -> 警告：可视化图片保存失败！")
#
#     assert score == 1, f"图片海陆比为 {details['ratio_value']}%，不符合 1 分标准"

# ==========================================
# 5. 测试不合格打分逻辑 (得 0 分) 全白
# ==========================================
def test_compute_land_sea_ratio_score_0_all_white(default_conf):
    """测试不合格情况：读取全白图片，并将特征区域染色保存"""
    img = cv2.imdecode(np.fromfile(ALL_WHITE_0, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert img is not None, f"错误：无法读取测试图片，请检查路径 -> {ALL_WHITE_0}"

    score, details = compute_land_sea_ratio(img, default_conf)
    print(f"\n[全白图片测试] 海陆比: {details['ratio_value']}%, 应该得分: 0, 实际得分: {score}")

    # 染色与保存逻辑
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    black_mask = cv2.inRange(gray, 0, 50)
    gray_mask = cv2.inRange(gray, 50, 200)

    vis_img = img.copy()
    vis_img[black_mask > 0] = (0, 255, 0)
    vis_img[gray_mask > 0] = (0, 0, 255)

    # 输出目录：相对于测试文件所在目录
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets", "test_data_land_sea_visual")
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.basename(ALL_WHITE_0)
    save_path = os.path.join(output_dir, f"visual_{filename}")

    is_success, buffer = cv2.imencode(".png", vis_img)
    if is_success:
        buffer.tofile(save_path)
        print(f" -> 可视化染色图已保存至: {save_path}")
    else:
        print(f" -> 警告：可视化图片保存失败！")

    assert score == 0, f"图片海陆比为 {details['ratio_value']}%，不符合 0 分标准"

# ==========================================
# 6. 测试不合格打分逻辑 (得 0 分) 很多黑线
# ==========================================
def test_compute_land_sea_ratio_score_0_much_black(default_conf):
    """测试不合格情况：读取黑线图片，并将特征区域染色保存"""
    img = cv2.imdecode(np.fromfile(MUCH_BLACK_0, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert img is not None, f"错误：无法读取测试图片，请检查路径 -> {MUCH_BLACK_0}"

    score, details = compute_land_sea_ratio(img, default_conf)
    print(f"\n[多黑线图片测试] 海陆比: {details['ratio_value']}%, 应该得分: 0, 实际得分: {score}")

    # 染色与保存逻辑
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    black_mask = cv2.inRange(gray, 0, 50)
    gray_mask = cv2.inRange(gray, 50, 200)

    vis_img = img.copy()
    vis_img[black_mask > 0] = (0, 255, 0)
    vis_img[gray_mask > 0] = (0, 0, 255)

    # 输出目录：相对于测试文件所在目录
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets", "test_data_land_sea_visual")
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.basename(MUCH_BLACK_0)
    save_path = os.path.join(output_dir, f"visual_{filename}")

    is_success, buffer = cv2.imencode(".png", vis_img)
    if is_success:
        buffer.tofile(save_path)
        print(f" -> 可视化染色图已保存至: {save_path}")
    else:
        print(f" -> 警告：可视化图片保存失败！")

    assert score == 0, f"图片海陆比为 {details['ratio_value']}%，不符合 0 分标准"
